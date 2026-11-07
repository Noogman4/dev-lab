#!/usr/bin/python3
"""In-memory stand-in for iptables/ip6tables and their -save/-restore tools.

Used only inside a capability-free bubblewrap sandbox. It is NOT netfilter: it
models table/chain bookkeeping and iptables-save normalisation well enough to
drive the real ufw Python code and ufw-init. Kernel semantics stay unproven.
"""

import copy
import json
import os
import random
import shlex
import sys

name = os.path.basename(sys.argv[0])
family = "6" if name.startswith("ip6") else "4"
path = f"/work/kernel/{family}.json"
BUILTIN = ("INPUT", "FORWARD", "OUTPUT")
TARGETS = {"ACCEPT", "DROP", "REJECT", "RETURN", "LOG"}
HEAD = ("-s", "-d", "-i", "-o", "-p")


class Fail(Exception):
    pass


def load():
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "pol": {b: "ACCEPT" for b in BUILTIN},
            "chains": {b: [] for b in BUILTIN},
        }


def save(state):
    with open(path, "w") as f:
        json.dump(state, f)


def host(value):
    if "/" in value or ":" not in value and not value[0].isdigit():
        return value
    return value + ("/128" if ":" in value else "/32")


def canon(tokens):
    """Reorder like iptables-save: address/iface/proto, matches, target."""
    head, matches, target = {}, [], []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in HEAD:
            head[tok] = tokens[i + 1]
            i += 2
        elif tok == "-j":
            target = [tok, tokens[i + 1]]
            i += 2
            while i < len(tokens) and tokens[i] != "-m":
                target.append(tokens[i])
                i += 1
        else:
            matches.append(tok)
            i += 1
    out = []
    for key in HEAD:
        if key in head:
            value = host(head[key]) if key in ("-s", "-d") else head[key]
            out += [key, value]
    proto = head.get("-p")
    if proto in ("tcp", "udp") and any(
        t in ("--dport", "--sport", "--dports") for t in matches
    ):
        if "-m" not in matches or matches[matches.index("-m") + 1] != proto:
            if "--dports" not in matches:
                out += ["-m", proto]
    if "--limit" in matches:
        i = matches.index("--limit")
        matches[i + 1] = (
            matches[i + 1].replace("/minute", "/min").replace("/second", "/sec")
        )
    if "--limit-burst" in matches:
        i = matches.index("--limit-burst")
        if matches[i + 1] == "5":
            del matches[i : i + 2]
    if "recent" in matches and "--name" not in matches:
        mask = (
            "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
            if family == "6"
            else "255.255.255.255"
        )
        matches += ["--name", "DEFAULT", "--mask", mask, "--rsource"]
    if proto == "ipv6-icmp" and "--icmpv6-type" in matches and "icmp6" not in matches:
        out += ["-m", "icmp6"]
    if proto == "icmp" and "--icmp-type" in matches and "-m" not in matches[:1]:
        out += ["-m", "icmp"]
    if target[:2] == ["-j", "REJECT"] and "--reject-with" not in target:
        target += [
            "--reject-with",
            "icmp6-port-unreachable" if family == "6" else "icmp-port-unreachable",
        ]
    return out + matches + target


def quote(token):
    if token == "" or any(c.isspace() or c in "\"'" for c in token):
        return '"%s"' % token.replace("\\", "\\\\").replace('"', '\\"')
    return token


def rule_text(tokens):
    return " ".join(quote(t) for t in canon(tokens))


def apply(state, argv):
    args = [a for a in argv]
    while args and args[0] in ("-w", "--wait"):
        args.pop(0)
    if args[:2] == ["-t", "filter"]:
        args = args[2:]
    elif args[:1] == ["-t"]:
        raise Fail("table")
    args = [a for a in args if a not in ("-n", "-v", "-w", "--line-numbers")]
    if not args:
        return ""
    op, rest = args[0], args[1:]
    chains = state["chains"]
    if op in ("-L", "-S"):
        if rest and rest[0] not in chains:
            raise Fail("no chain")
        wanted = rest[:1] or list(chains)
        return "\n".join(
            f"Chain {c}\ntarget prot opt source destination" for c in wanted
        )
    if op == "-N":
        if rest[0] in chains:
            raise Fail("exists")
        chains[rest[0]] = []
    elif op == "-X":
        for c in rest[:1] or [c for c in chains if c not in BUILTIN]:
            if c not in chains or chains[c]:
                raise Fail("cannot delete")
            if any(
                f"-j {c}" in r + " " or r.endswith(f"-j {c}")
                for v in chains.values()
                for r in v
            ):
                raise Fail("referenced")
            del chains[c]
    elif op in ("-F", "-Z"):
        if rest and rest[0] not in chains:
            raise Fail("no chain")
        if op == "-F":
            for c in rest[:1] or list(chains):
                chains[c] = []
    elif op == "-P":
        state["pol"][rest[0]] = rest[1]
    elif op in ("-A", "-I", "-D", "-C"):
        chain = rest[0]
        if chain not in chains:
            raise Fail("no chain")
        body = rest[1:]
        position = 0
        if op == "-I" and body and body[0].isdigit():
            position = int(body[0]) - 1
            body = body[1:]
        if "-j" in body:
            target = body[body.index("-j") + 1]
            if target not in TARGETS and target not in chains:
                raise Fail("no target " + target)
        text = rule_text(body)
        if op == "-A":
            chains[chain].append(text)
        elif op == "-I":
            chains[chain].insert(position, text)
        elif text in chains[chain]:
            if op == "-D":
                chains[chain].remove(text)
        else:
            raise Fail("no rule")
    else:
        raise Fail("unknown op " + op)
    return ""


def restore():
    args = sys.argv[1:]
    noflush = "-n" in args or "--noflush" in args
    state = copy.deepcopy(load())
    table = None
    for number, raw in enumerate(sys.stdin.read().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            if line.startswith("*"):
                table = line[1:]
                if table == "filter" and not noflush:
                    state = {
                        "pol": {b: "ACCEPT" for b in BUILTIN},
                        "chains": {b: [] for b in BUILTIN},
                    }
            elif line == "COMMIT":
                table = None
            elif table != "filter":
                continue
            elif line.startswith(":"):
                chain, policy = line[1:].split()[:2]
                if chain in BUILTIN:
                    if policy != "-":
                        state["pol"][chain] = policy
                else:
                    # Mirrors real restore: existing user chain is flushed.
                    state["chains"][chain] = []
            else:
                apply(state, shlex.split(line))
        except Fail as exc:
            print(f"{name}: line {number} failed: {exc}: {line}", file=sys.stderr)
            return 1
    save(state)
    return 0


def dump():
    state = load()
    print("# Generated by fake")
    print("*filter")
    for chain in state["chains"]:
        counters = f"[{random.randint(1, 999)}:{random.randint(1, 99999)}]"
        policy = state["pol"].get(chain, "-")
        print(f":{chain} {policy} {counters}")
    for chain, rules in state["chains"].items():
        for rule in rules:
            if os.path.exists("/work/kernel/quirk"):
                rule = rule.replace('[UFW BLOCK] "', '[UFW BLOCK]"')
            print(f"-A {chain} {rule}")
    print("COMMIT")
    return 0


def main():
    with open("/work/kernel/calls.log", "a") as log:
        log.write(" ".join(sys.argv) + "\n")
    if name.endswith("-restore"):
        if os.path.exists(f"/work/kernel/fail-{name}"):
            print(f"{name}: injected failure", file=sys.stderr)
            return 1
        return restore()
    if name.endswith("-save"):
        return dump()
    if name in ("sysctl", "modprobe"):
        return 0
    if len(sys.argv) > 1 and sys.argv[1] in ("-V", "--version"):
        print(
            "iptables v1.8.10 (nf_tables)"
            if family == "4"
            else "ip6tables v1.8.10 (nf_tables)"
        )
        return 0
    state = load()
    try:
        output = apply(state, sys.argv[1:])
    except (Fail, IndexError) as exc:
        print(f"{name}: {exc}", file=sys.stderr)
        return 1
    save(state)
    if output:
        print(output)
    return 0


sys.exit(main())
