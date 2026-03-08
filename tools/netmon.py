#!/usr/bin/env python3
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import time
import re
import shutil
import ipaddress
import json

# ---------- PATH Fix (wichtig bei Start über Desktop/Icon) ----------
DEFAULT_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
cur_path = os.environ.get("PATH", "")
if "/usr/sbin" not in cur_path:
    # keep existing PATH (e.g. user custom paths) and extend with defaults
    os.environ["PATH"] = (cur_path + ":" + DEFAULT_PATH) if cur_path else DEFAULT_PATH

VPN_CH = "proton"
VPN_DE = "proton-de"

# DNS Profile
DNS_PROFILES = {
    "System (DHCP/auto)": None,
    "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
    "Google (8.8.8.8)": ["8.8.8.8", "8.8.4.4"],
    "Quad9 (malware-blocking)": ["9.9.9.9", "149.112.112.112"],
}

TRACE_TARGETS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
    "ifconfig.me",
    "github.com",
    "cloudflare.com",
]


# ---------------- Safe command runner (NO shell) ----------------
def run_cmd(args, timeout=15, text=True):
    """
    args: list[str]
    returns (returncode, combined_output_str)
    """
    try:
        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=text,
            timeout=timeout,
            check=False,
        )
        out = (p.stdout or "").strip()
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "Command timed out"
    except Exception as e:
        return 1, f"Command failed: {e}"


def has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def ts():
    return datetime.now().strftime("%H:%M:%S")


def human_rate(bytes_per_sec: float) -> str:
    if bytes_per_sec < 0:
        bytes_per_sec = 0
    units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
    v = float(bytes_per_sec)
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    if i == 0:
        return f"{int(v)} {units[i]}"
    return f"{v:.1f} {units[i]}"


def is_safe_trace_target(target: str) -> bool:
    t = (target or "").strip()
    if not t:
        return False

    if re.search(r"[ \t\r\n;&|`$(){}[\]<>\\\"']", t):
        return False

    try:
        ipaddress.ip_address(t)
        return True
    except ValueError:
        pass

    if len(t) > 253:
        return False
    if t.endswith("."):
        t = t[:-1]
    labels = t.split(".")
    if any(len(lbl) == 0 or len(lbl) > 63 for lbl in labels):
        return False
    hostname_re = re.compile(r"^[A-Za-z0-9-]+$")
    for lbl in labels:
        if not hostname_re.match(lbl):
            return False
        if lbl.startswith("-") or lbl.endswith("-"):
            return False
    return True


def parse_traceroute_hops(output: str):
    hops = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue

        # traceroute output varies:
        #  3  192.168.1.1  1.23 ms
        #  3  router.local (192.168.1.1)  1.23 ms
        #  3  *
        #
        # Parse: hop number, token, optional IP in parentheses, optional RTT.
        m = re.match(
            r"^(\d+)\s+(\*|[^\s]+)(?:\s+\(?([0-9A-Fa-f\.:]+)\)?)?\s*(?:(\d+(?:\.\d+)?)\s*ms)?",
            line,
        )
        if m:
            hop = int(m.group(1))
            token = m.group(2)
            ip_in_paren = m.group(3)
            rtt = m.group(4)

            ip = token
            if ip_in_paren:
                ip = ip_in_paren

            hops.append(
                {
                    "hop": hop,
                    "ip": ip,
                    "rtt_ms": float(rtt) if rtt is not None else None,
                    "raw": line,
                }
            )
    return hops


def parse_cf_trace(output: str):
    info = {}
    for line in (output or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()
    return info


def parse_ss_lines(output: str):
    conns = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        proto = parts[0] if len(parts) > 0 else "?"
        state = "?"
        local = "?"
        remote = "?"

        if len(parts) >= 6:
            state = parts[1]
            local = parts[4]
            remote = parts[5]
        elif len(parts) >= 5:
            state = parts[1]
            local = parts[3]
            remote = parts[4]

        pid = ""
        proc = ""

        um = re.search(r'users:\(\((.+)\)\)', line)
        if um:
            blob = um.group(1)
            nm = re.search(r'"([^"]+)"', blob)
            pm = re.search(r'pid=(\d+)', blob)
            if nm:
                proc = nm.group(1)
            if pm:
                pid = pm.group(1)

        conns.append({
            "proto": proto,
            "state": state,
            "local": local,
            "remote": remote,
            "pid": pid,
            "proc": proc,
            "raw": line,
        })
    return conns


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ----- Locks gegen "Schaltchaos" -----
        self.ufw_lock = threading.Lock()

        # ---------------- Desktop-Scaling / Kompakt ----------------
        try:
            self.tk.call("tk", "scaling", 0.90)
        except Exception:
            pass

        style = ttk.Style(self)
        style.configure("TButton", padding=(6, 3))
        style.configure("TCheckbutton", padding=(4, 2))

        self.title("NetMon – Firewall, VPN, DNS, Trace (Pi)")

        # Fenstergröße dynamisch: 85% vom Screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = int(sw * 0.85)
        h = int(sh * 0.85)
        self.geometry(f"{w}x{h}")
        self.minsize(900, 600)

        # state
        self.last_dns_consistency_ok = None   # True/False/None
        self.last_dns_consistency_ts = 0.0
        self.dns_consistency_running = False

        self.last_ip_ts = 0.0
        self.ip_country_running = False
        self.public_ip = "–"
        self.country = "–"

        self.last_wg_transfer = None
        self.last_wg_ts = None
        self.wg_rx_rate = 0.0
        self.wg_tx_rate = 0.0

        self.nm_dns_header_text = "NM DNS: –"

        # privacy: external calls toggle (safer default)
        self.auto_external_checks = tk.BooleanVar(value=False)
        
        # Hop Lookup (Land/Provider) – optional (Privacy)
        self.hop_lookup_enabled = tk.BooleanVar(value=False)
        self.hop_cache = {}  # ip -> (country_code, org)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------- Global scroll (whole page) ----------
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        self.page_canvas = tk.Canvas(outer, highlightthickness=0)
        self.page_canvas.pack(side="left", fill="both", expand=True)

        page_scroll = ttk.Scrollbar(outer, orient="vertical", command=self.page_canvas.yview)
        page_scroll.pack(side="right", fill="y")

        self.page_canvas.configure(yscrollcommand=page_scroll.set)

        self.page = ttk.Frame(self.page_canvas, padding=0)
        self.page_window = self.page_canvas.create_window((0, 0), window=self.page, anchor="nw")

        def _on_page_config(_event):
            self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

        def _on_canvas_config(event):
            self.page_canvas.itemconfig(self.page_window, width=event.width)

        self.page.bind("<Configure>", _on_page_config)
        self.page_canvas.bind("<Configure>", _on_canvas_config)

        def _bind_scroll(_e=None):
            self.page_canvas.bind_all("<Button-4>", self._scroll_up)
            self.page_canvas.bind_all("<Button-5>", self._scroll_down)

        def _unbind_scroll(_e=None):
            self.page_canvas.unbind_all("<Button-4>")
            self.page_canvas.unbind_all("<Button-5>")

        self.page_canvas.bind("<Enter>", _bind_scroll)
        self.page_canvas.bind("<Leave>", _unbind_scroll)

        # ---------- Build content inside self.page ----------
        self.page.columnconfigure(1, weight=1)

        header = ttk.Frame(self.page, padding=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Status", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.status_text = ttk.Label(header, text="–")
        self.status_text.grid(row=0, column=1, sticky="w", padx=10)

        self.dns_header = ttk.Label(header, text=self.nm_dns_header_text)
        self.dns_header.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # main area
        left = ttk.Frame(self.page, padding=10)
        left.grid(row=1, column=0, sticky="n")

        right = ttk.Frame(self.page, padding=10)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Ampel
        amp = ttk.LabelFrame(left, text="Ampel", padding=10)
        amp.pack(fill="x")

        self.l_inet = self.make_light(amp, "Internet")
        self.l_vpn = self.make_light(amp, "VPN (WireGuard)")
        self.l_fw = self.make_light(amp, "Firewall (UFW)")
        self.l_ks = self.make_light(amp, "Killswitch (UFW VPN-only)")
        self.l_dnscons = self.make_light(amp, "DNS-Konsistenztest")
        self.l_ipv6 = self.make_light(amp, "IPv6")

        # Aktionen
        ctl = ttk.LabelFrame(left, text="Aktionen", padding=10)
        ctl.pack(fill="x", pady=10)

        ttk.Button(ctl, text="Firewall EIN", command=self.fw_enable).pack(fill="x")
        ttk.Button(ctl, text="Firewall AUS", command=self.fw_disable).pack(fill="x", pady=5)
        ttk.Button(ctl, text="Firewall Status", command=self.fw_status).pack(fill="x")

        ttk.Separator(ctl).pack(fill="x", pady=10)

        ttk.Button(ctl, text="VPN CH", command=lambda: self.vpn_switch(VPN_CH)).pack(fill="x")
        ttk.Button(ctl, text="VPN DE", command=lambda: self.vpn_switch(VPN_DE)).pack(fill="x", pady=5)
        ttk.Button(ctl, text="VPN AUS", command=self.vpn_off).pack(fill="x")

        ttk.Separator(ctl).pack(fill="x", pady=10)

        ttk.Button(ctl, text="Killswitch AN", command=self.killswitch_on).pack(fill="x")
        ttk.Button(ctl, text="Killswitch AUS", command=self.killswitch_off).pack(fill="x", pady=5)

        ttk.Separator(ctl).pack(fill="x", pady=10)

        ttk.Button(ctl, text="SSH Regel entfernen (UFW)", command=self.remove_ssh_rule_async).pack(fill="x")

        # IPv6
        ipv6f = ttk.LabelFrame(left, text="IPv6", padding=10)
        ipv6f.pack(fill="x", pady=10)

        ttk.Button(ipv6f, text="IPv6 AN", command=self.ipv6_enable).pack(fill="x")
        ttk.Button(ipv6f, text="IPv6 AUS", command=self.ipv6_disable).pack(fill="x", pady=6)

        # DNS Dropdown
        dnsf = ttk.LabelFrame(left, text="DNS Resolver (Dropdown)", padding=10)
        dnsf.pack(fill="x", pady=10)

        self.dns_choice = tk.StringVar(value="System (DHCP/auto)")
        self.dns_combo = ttk.Combobox(
            dnsf,
            textvariable=self.dns_choice,
            values=list(DNS_PROFILES.keys()),
            state="readonly",
        )
        self.dns_combo.pack(fill="x")

        ttk.Button(dnsf, text="DNS anwenden", command=self.apply_dns).pack(fill="x", pady=6)
        ttk.Button(dnsf, text="DNS Status (nmcli)", command=self.show_dns_status).pack(fill="x")
        ttk.Button(dnsf, text="DNS-Konsistenztest", command=lambda: self.dns_consistency_check_async(force=True)).pack(fill="x", pady=6)


        # ---------- RIGHT: THEMENFELDER oben + Tabs ----------
        action_bar = ttk.Frame(right)
        action_bar.grid(row=0, column=0, sticky="ew")
        for i in range(4):
            action_bar.columnconfigure(i, weight=1)

        # Thema: Egress
        eg = ttk.LabelFrame(action_bar, text="Egress", padding=8)
        eg.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(eg, text="Whoami (Egress)", command=lambda: self.whoami_async(force=True)).pack(fill="x")
        ttk.Button(eg, text="IP + Land holen", command=lambda: self.ip_country_async(force=True)).pack(fill="x", pady=(6, 0))

        # Thema: DNS
        dnst = ttk.LabelFrame(action_bar, text="DNS", padding=8)
        dnst.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(dnst, text="DNS Status (resolv*)", command=self.resolved_status_async).pack(fill="x")
        ttk.Button(dnst, text="DNS-Konsistenztest", command=lambda: self.dns_consistency_check_async(force=True)).pack(fill="x", pady=(6, 0))

        # Thema: Verbindungen
        ct = ttk.LabelFrame(action_bar, text="Verbindungen", padding=8)
        ct.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        ttk.Button(ct, text="Verbindungen (PID) aktualisieren", command=self.connections_async).pack(fill="x")
        ttk.Button(ct, text="ARP Tabelle (arp -a)", command=self.arp_async).pack(fill="x", pady=(6, 0))
        ttk.Button(ct, text="Routing Tabelle (ip route)", command=self.route_async).pack(fill="x", pady=(6, 0))

        # Thema: Trace
        tr = ttk.LabelFrame(action_bar, text="Trace", padding=8)
        tr.grid(row=0, column=3, sticky="ew")
        self.trace_target = tk.StringVar(value=TRACE_TARGETS[0])
        self.trace_combo = ttk.Combobox(tr, textvariable=self.trace_target, values=TRACE_TARGETS, state="normal")
        self.trace_combo.pack(fill="x")
        ttk.Button(tr, text="Trace starten (Log)", command=self.trace_async).pack(fill="x", pady=(6, 0))
        ttk.Button(tr, text="Trace starten (Hops)", command=self.trace_table_async).pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(tr, text="Hop Lookup (Land/Provider)", variable=self.hop_lookup_enabled).pack(fill="x", pady=(6, 0))
        
        self.nb = ttk.Notebook(right)
        self.nb.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        # Tab: Log
        self.tab_log = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_log, text="Log")

        log_bar = ttk.Frame(self.tab_log)
        log_bar.pack(fill="x", pady=(0, 8))
        ttk.Button(log_bar, text="Log leeren", command=self.clear_log).pack(side="right")

        self.text = tk.Text(self.tab_log, wrap="word")
        self.text.pack(fill="both", expand=True)

        # Tab: Trace (Hops)
        self.tab_trace = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_trace, text="Trace (Hops)")

        self.trace_table = ttk.Treeview(
            self.tab_trace,
            columns=("hop", "ip", "rtt", "cc", "org"),            show="headings",
            height=18,
        )
        self.trace_table.heading("hop", text="Hop")
        self.trace_table.heading("ip", text="IP")
        self.trace_table.heading("rtt", text="RTT (ms)")
        self.trace_table.column("hop", width=60, anchor="center")
        self.trace_table.column("ip", width=260, anchor="w")
        self.trace_table.column("rtt", width=120, anchor="e")
        self.trace_table.column("cc", width=70, anchor="center")
        self.trace_table.column("org", width=220, anchor="w")
        self.trace_table.pack(fill="both", expand=True)
        self.trace_table.heading("cc", text="Land")
        self.trace_table.heading("org", text="Provider")
        
        # Tab: Connections (PID)
        self.tab_conn = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_conn, text="Verbindungen (PID)")

        conn_top = ttk.Frame(self.tab_conn)
        conn_top.pack(fill="x", pady=(0, 8))
        ttk.Label(conn_top, text="Filter (optional):").pack(side="left")
        self.conn_filter = tk.StringVar(value="")
        ttk.Entry(conn_top, textvariable=self.conn_filter).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(conn_top, text="Filter anwenden", command=self.apply_conn_filter).pack(side="left")

        self.conn_table = ttk.Treeview(
            self.tab_conn,
            columns=("proto", "state", "local", "remote", "pid", "proc"),
            show="headings",
            height=18,
        )
        for col, title, w in [
            ("proto", "Proto", 70),
            ("state", "State", 90),
            ("local", "Local", 220),
            ("remote", "Remote", 220),
            ("pid", "PID", 70),
            ("proc", "Process", 160),
        ]:
            self.conn_table.heading(col, text=title)
            self.conn_table.column(col, width=w, anchor="w")
        self.conn_table.column("pid", anchor="center")
        self.conn_table.pack(fill="both", expand=True)

        self._conn_rows_cache = []

        # Tab: DNS Status
        self.tab_dns = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_dns, text="DNS Status")

        dns_bar = ttk.Frame(self.tab_dns)
        dns_bar.pack(fill="x", pady=(0, 8))
        ttk.Button(dns_bar, text="DNS Status aktualisieren", command=self.resolved_status_async).pack(side="left")
        ttk.Button(dns_bar, text="Tabs: Log", command=lambda: self.nb.select(self.tab_log)).pack(side="left", padx=8)

        self.dns_text = tk.Text(self.tab_dns, wrap="word")
        self.dns_text.pack(fill="both", expand=True)

        bottom = ttk.Frame(self.page, padding=10)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.log("Start.")
        self.refresh()
        self.after(5000, self.auto_refresh)

    # scroll helpers (Linux wheel)
    def _scroll_up(self, _e):
        self.page_canvas.yview_scroll(-1, "units")

    def _scroll_down(self, _e):
        self.page_canvas.yview_scroll(1, "units")

    def on_close(self):
        self.destroy()

    # ---------- UI helpers ----------
    def make_light(self, parent, label):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=4)
        c = tk.Canvas(f, width=18, height=18, highlightthickness=0)
        c.pack(side="left")
        dot = c.create_oval(2, 2, 16, 16, fill="gray")
        ttk.Label(f, text=label).pack(side="left", padx=8)
        return c, dot

    def set_light(self, light, color):
        light[0].itemconfig(light[1], fill=color)

    def log(self, msg):
        self.text.insert("end", f"[{ts()}] {msg}\n")
        self.text.see("end")
        
    def run_async(self, func):
        threading.Thread(target=func, daemon=True).start()

    def clear_log(self):
        self.text.delete("1.0", "end")

    # ---------- IPv6 ----------
    def ipv6_is_disabled(self) -> bool:
        # Prefer /proc (per-interface flags) when available
        try:
            base = "/proc/sys/net/ipv6/conf"
            if os.path.isdir(base):
                all_p = os.path.join(base, "all", "disable_ipv6")
                if os.path.exists(all_p):
                    v = open(all_p, "r").read().strip()
                    if v == "1":
                        return True

                # Consider IPv6 enabled if any interface flag is 0
                for entry in os.listdir(base):
                    p = os.path.join(base, entry, "disable_ipv6")
                    if os.path.exists(p) and open(p, "r").read().strip() == "0":
                        return False

                return True
        except Exception:
            pass

        # Fallback via sysctl
        _, out = run_cmd(["sysctl", "-n", "net.ipv6.conf.all.disable_ipv6"], timeout=3)
        return out.strip() == "1"

    def ipv6_disable(self):
        cmds = [
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"],
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"],
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.lo.disable_ipv6=1"],
        ]
        for c in cmds:
            rc, out = run_cmd(c, timeout=6)
            if rc != 0 and out:
                self.log(out)
        self.log("IPv6: deaktiviert (sysctl; nicht persistent nach Reboot).")
        self.refresh()

    def ipv6_enable(self):
        cmds = [
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"],
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=0"],
            ["sudo", "-n", "sysctl", "-w", "net.ipv6.conf.lo.disable_ipv6=0"],
        ]
        for c in cmds:
            rc, out = run_cmd(c, timeout=6)
            if rc != 0 and out:
                self.log(out)
        self.log("IPv6: aktiviert (sysctl; nicht persistent nach Reboot).")
        self.refresh()

    # ---------- Network detect ----------
    def get_default_iface(self):
        _, out = run_cmd(["ip", "route", "show", "default"], timeout=3)
        parts = out.split()
        for i, p in enumerate(parts):
            if p == "dev" and i + 1 < len(parts):
                return parts[i + 1]
        return "eth0"

    def nm_active_connections(self):
        _, out = run_cmd(["nmcli", "-t", "-f", "NAME,DEVICE", "con", "show", "--active"], timeout=5)
        res = []
        for line in (out or "").splitlines():
            if ":" in line:
                n, d = line.split(":", 1)
                if n and d:
                    res.append((n, d))
        return res

    def nm_active_conn_for_dev(self, dev: str):
        for n, d in self.nm_active_connections():
            if d == dev:
                return n
        return None

    def check_internet(self):
        try:
            p = subprocess.run(
                ["ping", "-c", "1", "-W", "1", "1.1.1.1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
                text=True,
            )
            return p.returncode == 0
        except Exception:
            return False

    def active_wg_profile(self):
        _, out = run_cmd(["wg", "show", "interfaces"], timeout=3)
        if VPN_CH in out.split():
            return VPN_CH
        if VPN_DE in out.split():
            return VPN_DE
        return None

    def get_wg_iface(self):
        _, out = run_cmd(["wg", "show", "interfaces"], timeout=3)
        if not out.strip():
            return None
        if VPN_DE in out.split():
            return VPN_DE
        if VPN_CH in out.split():
            return VPN_CH
        return out.split()[0]

    # ---------- UFW status robust + LOCK ----------
    def check_ufw_active(self):
        with self.ufw_lock:
            rc, out = run_cmd(["sudo", "-n", "ufw", "status"], timeout=8)
        if rc != 0:
            return False

        t = (out or "").strip().lower()

        # OFF keywords (DE/EN)
        if "inactive" in t or "inaktiv" in t:
            return False

        # ON keywords (DE/EN)
        if "status:" in t and ("status: active" in t or "status: aktiv" in t or " active" in t or " aktiv" in t):
            return True

        # Fallback: wenn "Status:" vorkommt und NICHT inaktiv ist, ist es i.d.R. aktiv
        if "status:" in t and ("inactive" not in t) and ("inaktiv" not in t):
            return True

        return False

    def killswitch_is_on(self):
        # Robust: prüft Default-Policy outgoing (DE/EN), nicht nur "deny (outgoing)" Text
        with self.ufw_lock:
            rc, out = run_cmd(["sudo", "-n", "ufw", "status", "verbose"], timeout=12)

        if rc != 0:
            return False

        t = (out or "").lower()

        # EN: "Default: deny (incoming), allow (outgoing), disabled (routed)"
        # DE: "Voreinstellung: deny (eingehend), allow (abgehend), disabled (gesendet)"
        # Killswitch AN setzt: default deny outgoing -> also "deny (outgoing/abgehend)"
        if "default:" in t:
            # outgoing deny?
            if "deny (outgoing)" in t:
                return True
            # outgoing allow?
            if "allow (outgoing)" in t:
                return False

        if "voreinstellung:" in t:
            if "deny (abgehend)" in t:
                return True
            if "allow (abgehend)" in t:
                return False

        # Fallback: alte Methode
        return ("deny (outgoing)" in t) or ("deny (abgehend)" in t)
        
    # ---------- NM DNS header ----------
    def nm_get_dns_list(self, iface: str):
        _, out = run_cmd(["nmcli", "-g", "IP4.DNS", "dev", "show", iface], timeout=5)
        if not out.strip():
            return []
        return [ln.strip() for ln in out.splitlines() if ln.strip()]

    def update_dns_header(self):
        iface = self.get_default_iface()
        dns = self.nm_get_dns_list(iface) if has_cmd("nmcli") else []
        v6 = "IPv6 AUS" if self.ipv6_is_disabled() else "IPv6 AN"
        if dns:
            self.nm_dns_header_text = f"NM DNS ({iface}): " + ", ".join(dns) + f" | {v6}"
        else:
            self.nm_dns_header_text = f"NM DNS ({iface}): – | {v6}"
        self.dns_header.config(text=self.nm_dns_header_text)

    # ---------- WG RX/TX ----------
    def read_wg_transfer(self):
        res = {}
        rc, out = run_cmd(["sudo", "-n", "wg", "show", "all", "transfer"], timeout=6)
        if out.strip() and rc == 0:
            for line in out.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3:
                    iface = parts[0]
                    try:
                        rx = int(parts[1])
                        tx = int(parts[2])
                        res[iface] = (rx, tx)
                    except ValueError:
                        pass
        if res:
            return res

        wg_if = self.get_wg_iface()
        if not wg_if:
            return {}

        rc, out = run_cmd(["sudo", "-n", "wg", "show", wg_if, "transfer"], timeout=6)
        total_rx = 0
        total_tx = 0
        if out.strip() and rc == 0:
            for line in out.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        rx = int(parts[1])
                        tx = int(parts[2])
                        total_rx += rx
                        total_tx += tx
                    except ValueError:
                        pass
            res[wg_if] = (total_rx, total_tx)
        return res

    def update_wg_rates(self):
        now = time.time()
        transfer = self.read_wg_transfer()
        wg_if = self.get_wg_iface()

        if not wg_if or wg_if not in transfer:
            self.wg_rx_rate = 0.0
            self.wg_tx_rate = 0.0
            self.last_wg_transfer = transfer
            self.last_wg_ts = now
            return wg_if, None

        cur_rx, cur_tx = transfer[wg_if]

        if self.last_wg_transfer is None or self.last_wg_ts is None or wg_if not in self.last_wg_transfer:
            self.last_wg_transfer = transfer
            self.last_wg_ts = now
            self.wg_rx_rate = 0.0
            self.wg_tx_rate = 0.0
            return wg_if, (cur_rx, cur_tx)

        dt = max(0.5, now - self.last_wg_ts)
        prev_rx, prev_tx = self.last_wg_transfer[wg_if]

        self.wg_rx_rate = (cur_rx - prev_rx) / dt
        self.wg_tx_rate = (cur_tx - prev_tx) / dt

        self.last_wg_transfer = transfer
        self.last_wg_ts = now
        return wg_if, (cur_rx, cur_tx)

    # ---------- DNS apply ----------
    def apply_dns(self):
        if not has_cmd("nmcli"):
            self.log("nmcli fehlt – NetworkManager ist nicht verfügbar (Pi OS nutzt oft dhcpcd).")
            return

        iface = self.get_default_iface()
        con = self.nm_active_conn_for_dev(iface)
        if not con:
            self.log(f"Keine aktive NetworkManager-Connection für {iface} gefunden.")
            return

        choice = self.dns_choice.get()
        servers = DNS_PROFILES.get(choice)

        if servers is None:
            cmds = [
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.ignore-auto-dns", "no"],
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.dns", ""],
                ["sudo", "-n", "nmcli", "con", "up", con],
            ]
            for c in cmds:
                rc, out = run_cmd(c, timeout=12)
                if rc != 0 and out:
                    self.log(out)
            self.log(f"DNS: System(auto) für '{con}' ({iface}).")
            self.last_dns_consistency_ok = None
            self.last_dns_consistency_ts = 0.0
            self.refresh()
            return

        dns_str = " ".join(servers)
        cmds = [
            ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.ignore-auto-dns", "yes"],
            ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.dns", dns_str],
            ["sudo", "-n", "nmcli", "con", "up", con],
        ]
        for c in cmds:
            rc, out = run_cmd(c, timeout=12)
            if rc != 0:
                self.log("DNS setzen fehlgeschlagen (sudo/NOPASSWD?).")
                if out:
                    self.log(out)
                return

        self.log(f"DNS gesetzt: {choice} -> {dns_str} (Connection '{con}' / {iface})")
        self.last_dns_consistency_ok = None
        self.last_dns_consistency_ts = 0.0
        self.refresh()

    def show_dns_status(self):
        if not has_cmd("nmcli"):
            self.log("nmcli fehlt – NetworkManager ist nicht verfügbar.")
            return
        iface = self.get_default_iface()
        _, out = run_cmd(["nmcli", "dev", "show", iface], timeout=8)
        if not out:
            self.log("Kein nmcli Output.")
            return
        lines = [ln for ln in out.splitlines() if "IP4.DNS" in ln or "IP4.DOMAIN" in ln]
        self.log("\n".join(lines) if lines else out)

    # ---------- DNS Consistency check ----------
    def dns_consistency_check_async(self, force=False):
        if self.dns_consistency_running:
            return
        if not force and (time.time() - self.last_dns_consistency_ts) < 30:
            return

        if not (has_cmd("dig") or has_cmd("nslookup")):
            self.log("DNS-Test: weder 'dig' noch 'nslookup' gefunden. Install: sudo apt install dnsutils")
            self.last_dns_consistency_ok = None
            self.last_dns_consistency_ts = time.time()
            return

        self.dns_consistency_running = True

        def job():
            try:
                choice = self.dns_choice.get()
                selected = DNS_PROFILES.get(choice)
                test_domain = "example.com"

                def sys_query():
                    if has_cmd("dig"):
                        _, out = run_cmd(["dig", "+time=2", "+tries=1", "+short", "A", test_domain], timeout=5)
                        return out.strip()
                    _, out = run_cmd(["nslookup", "-timeout=2", test_domain], timeout=5)
                    return out.strip()

                def explicit_query(server: str):
                    if has_cmd("dig"):
                        _, out = run_cmd(["dig", "+time=2", "+tries=1", "+short", "A", test_domain, f"@{server}"], timeout=5)
                        return out.strip()
                    _, out = run_cmd(["nslookup", "-timeout=2", test_domain, server], timeout=5)
                    return out.strip()

                sys_ok = bool(sys_query())

                if selected is None:
                    self.last_dns_consistency_ok = None
                    self.last_dns_consistency_ts = time.time()
                    self.after(0, lambda: self.log(f"DNS-Konsistenz: System(auto). DNS answer: {'OK' if sys_ok else '—'}"))
                    return

                explicit_results = [(s, bool(explicit_query(s))) for s in selected]
                any_explicit_ok = any(ok for _, ok in explicit_results)

                if (not sys_ok) and (not any_explicit_ok):
                    self.last_dns_consistency_ok = None
                    self.last_dns_consistency_ts = time.time()
                    self.after(0, lambda: self.log(
                        "DNS-Konsistenz: Keine DNS-Antworten (System + explizit). Ergebnis: nicht testbar (grau)."
                    ))
                    return

                ok = sys_ok and any_explicit_ok
                self.last_dns_consistency_ok = ok
                self.last_dns_consistency_ts = time.time()

                def log_it():
                    self.log(f"DNS-Konsistenz: System DNS answer: {'OK' if sys_ok else '—'}")
                    self.log("DNS-Konsistenz: Explizit gewählt: " + ", ".join([f"{s}->{('OK' if ok2 else '—')}" for s, ok2 in explicit_results]))
                    self.log("DNS-Konsistenz Ergebnis: " + ("OK" if ok else "MÖGLICHE Abweichung (System/Resolver)"))
                self.after(0, log_it)

            finally:
                self.dns_consistency_running = False

        threading.Thread(target=job, daemon=True).start()

    # ---------- Actions ----------
    def fw_enable(self):

        def job():
            if self.check_ufw_active():
                self.after(0, lambda: self.log("Firewall ist bereits aktiv."))
                return

            rc, out = run_cmd(["sudo", "-n", "ufw", "--force", "enable"], timeout=40)

            if rc != 0:
                self.after(0, lambda: self.log("Firewall konnte NICHT aktiviert werden"))
                if out:
                    self.after(0, lambda: self.log(out))
            else:
                self.after(0, lambda: self.log("Firewall aktiviert."))

            self.after(0, self.refresh)

        self.run_async(job)
        

    def fw_status(self):
        with self.ufw_lock:
            _, out = run_cmd(["sudo", "-n", "ufw", "status", "verbose"], timeout=12)
        self.log(out)
        
    def fw_disable(self):

        def job():
            if not self.check_ufw_active():
                self.after(0, lambda: self.log("Firewall ist bereits deaktiviert."))
                return

            rc, out = run_cmd(["sudo", "-n", "ufw", "disable"], timeout=40)

            if rc != 0:
                self.after(0, lambda: self.log("Firewall konnte NICHT deaktiviert werden"))
                if out:
                    self.after(0, lambda: self.log(out))
            else:
                self.after(0, lambda: self.log("Firewall deaktiviert."))

            self.after(0, self.refresh)

        self.run_async(job)
    
    def vpn_switch(self, target):
        other = VPN_DE if target == VPN_CH else VPN_CH
        run_cmd(["sudo", "-n", "wg-quick", "down", other], timeout=12)
        rc, out = run_cmd(["sudo", "-n", "wg-quick", "up", target], timeout=20)
        self.log(out or f"VPN gestartet: {target}")
        if rc != 0:
            self.log("VPN Start fehlgeschlagen (Output oben).")
        self.last_wg_transfer = None
        self.last_wg_ts = None
        self.refresh()

    def vpn_off(self):
        run_cmd(["sudo", "-n", "wg-quick", "down", VPN_CH], timeout=12)
        run_cmd(["sudo", "-n", "wg-quick", "down", VPN_DE], timeout=12)
        self.log("VPN deaktiviert.")
        if self.killswitch_is_on():
            self.log("HINWEIS: Killswitch ist AN – ohne VPN evtl. kein Internet (gewollt).")
        self.refresh()

    def killswitch_on(self):
        def job():
            wg_if = self.get_wg_iface()
            if not wg_if:
                self.after(0, lambda: self.log("VPN ist nicht aktiv – Killswitch kann nicht aktiviert werden."))
                return

            # UFW-Befehle seriell ausführen (kein GUI freeze, kein Lock-Deadlock)
            with self.ufw_lock:
                # UFW sicher aktivieren (nicht check_ufw_active() benutzen -> würde locken)
                rc_s, out_s = run_cmd(["sudo", "-n", "ufw", "status"], timeout=10)
                t = (out_s or "").lower()
                ufw_on = (rc_s == 0) and ("status:" in t) and ("inaktiv" not in t) and ("inactive" not in t)

                if not ufw_on:
                    run_cmd(["sudo", "-n", "ufw", "--force", "enable"], timeout=20)

                cmds = [
                    ["sudo", "-n", "ufw", "default", "deny", "outgoing"],
                    ["sudo", "-n", "ufw", "default", "deny", "incoming"],
                    ["sudo", "-n", "ufw", "allow", "in", "on", "lo"],
                    ["sudo", "-n", "ufw", "allow", "out", "on", "lo"],
                    ["sudo", "-n", "ufw", "allow", "out", "on", wg_if],
                ]
                for c in cmds:
                    run_cmd(c, timeout=20)

            self.after(0, lambda: self.log(f"Killswitch AN – nur OUT über {wg_if} erlaubt (plus Loopback)."))
            self.after(0, self.refresh)

        self.run_async(job)
        
    def killswitch_off(self):
        def job():
            with self.ufw_lock:
                cmds = [
                    ["sudo", "-n", "ufw", "default", "allow", "outgoing"],
                    ["sudo", "-n", "ufw", "default", "deny", "incoming"],
                ]
                for c in cmds:
                    run_cmd(c, timeout=20)

            self.after(0, lambda: self.log("Killswitch AUS – normales Routing wieder aktiv."))
            self.after(0, self.refresh)

        self.run_async(job)
        
    def remove_ssh_rule_async(self, auto=False):
        if not auto:
            ok = messagebox.askyesno(
                "Achtung",
                "Das entfernt UFW-Regeln für SSH (Port 22).\n"
                "Wenn du per SSH verbunden bist, kannst du dich aussperren.\n\n"
                "Wirklich fortfahren?"
            )
            if not ok:
                self.log("SSH/UFW: Abgebrochen.")
                return

        def job():
            with self.ufw_lock:
                _, out = run_cmd(["sudo", "-n", "ufw", "status", "numbered"], timeout=12)
            if not out.strip():
                self.after(0, lambda: self.log("UFW status numbered leer/unverfügbar."))
                return

            matches = []
            for line in out.splitlines():
                m = re.match(r"^\[\s*(\d+)\]\s+(.*)$", line.strip())
                if not m:
                    continue
                num = int(m.group(1))
                rest = m.group(2)
                if re.search(r"(^|[^0-9])22([^0-9]|$)", rest):
                    matches.append((num, rest))

            if not matches:
                self.after(0, lambda: self.log("SSH/UFW: keine Port-22-Regel gefunden."))
                return

            matches.sort(key=lambda x: x[0], reverse=True)
            for num, rest in matches:
                with self.ufw_lock:
                    rc2, del_out = run_cmd(["sudo", "-n", "ufw", "--force", "delete", str(num)], timeout=12)
                if rc2 == 0:
                    self.after(0, lambda r=rest: self.log(f"SSH/UFW entfernt: {r}"))
                else:
                    self.after(0, lambda o=del_out: self.log(f"SSH/UFW delete failed: {o}"))

            self.after(0, self.refresh)

        threading.Thread(target=job, daemon=True).start()

    # ---------- Trace (Log) ----------
    def trace_async(self):
        target = (self.trace_target.get() or "").strip()
        if not target:
            self.log("Bitte Ziel für Trace eingeben.")
            return
        if not is_safe_trace_target(target):
            self.log("Trace-Ziel ungültig/unsicher. Erlaubt: IP oder Hostname (ohne Sonderzeichen/Leerzeichen).")
            return

        def job():
            self.after(0, lambda: self.log(f"Trace gestartet (Log): {target}"))

            out = ""
            rc = 1

            if has_cmd("tracepath"):
                rc, out = run_cmd(["tracepath", "-n", "-m", "20", target], timeout=25)

            if (rc != 0) and has_cmd("traceroute"):
                rc, out = run_cmd(["traceroute", "-n", "-T", "-p", "443", "-m", "20", target], timeout=35)

            self.after(0, lambda: self.log(out or "Trace fehlgeschlagen (tracepath/traceroute fehlt?)."))

        threading.Thread(target=job, daemon=True).start()

    # ---------- Trace (Table of hops) ----------
    def hop_lookup(self, ip: str):
        ip = (ip or "").strip()
        if not ip or ip == "*" or ":" in ip:
            return "", ""

        # cache hit?
        if ip in self.hop_cache:
            return self.hop_cache[ip]

        # privacy: only when enabled
        if not self.hop_lookup_enabled.get():
            self.hop_cache[ip] = ("", "")
            return "", ""

        # skip private/reserved/non-global IPs (no external lookup)
        try:
            ip_obj = ipaddress.ip_address(ip)
            if not ip_obj.is_global:
                self.hop_cache[ip] = ("", "")
                return "", ""
        except ValueError:
            # if it's not an IP, we don't look it up here
            self.hop_cache[ip] = ("", "")
            return "", ""

        # ipwho.is returns JSON with country_code + org
        rc, out = run_cmd(
            ["curl", "-s", "--fail", "--max-time", "3", f"https://ipwho.is/{ip}"],
            timeout=5,
        )
        if rc != 0 or not out:
            self.hop_cache[ip] = ("", "")
            return "", ""

        try:
            data = json.loads(out)
            if not data.get("success", True):
                self.hop_cache[ip] = ("", "")
                return "", ""

            cc = (data.get("country_code") or "").strip()
            org = (data.get("org") or data.get("connection", {}).get("org") or "").strip()
            self.hop_cache[ip] = (cc, org)
            return cc, org
        except Exception:
            self.hop_cache[ip] = ("", "")
            return "", ""

    def trace_table_async(self):
        target = (self.trace_target.get() or "").strip()
        if not target:
            self.log("Bitte Ziel für Trace eingeben.")
            return
        if not is_safe_trace_target(target):
            self.log("Trace-Ziel ungültig/unsicher. Erlaubt: IP oder Hostname (ohne Sonderzeichen/Leerzeichen).")
            return
        if not has_cmd("traceroute"):
            self.log("Für Hops-Tabelle wird 'traceroute' benötigt (sudo apt install traceroute).")
            return

        def clear_table():
            for item in self.trace_table.get_children():
                self.trace_table.delete(item)

        def job():
            self.after(0, lambda: (self.nb.select(self.tab_trace), clear_table(), self.log(f"Trace gestartet (Hops): {target}")))
            rc, out = run_cmd(["traceroute", "-n", "-q", "1", "-m", "20", target], timeout=35)
            hops = parse_traceroute_hops(out)

            def fill():
                if not out.strip():
                    self.log("Traceroute ohne Output.")
                    return
                if rc != 0:
                    self.log(f"Traceroute returncode={rc} (Output folgt)")
                    self.log(out)

                for h in hops:
                    rtt = "" if h["rtt_ms"] is None else f"{h['rtt_ms']:.2f}" 
                    
                    # Land / Provider Lookup
                    cc, org = self.hop_lookup(h["ip"])
                    
                    self.trace_table.insert(
                        "",
                        "end",
                        values=(h["hop"], h["ip"], rtt, cc, org)
                    )
                    
                if not hops:
                    self.log(out)

            self.after(0, fill)

        threading.Thread(target=job, daemon=True).start()

    # ---------- Whoami / Egress info ----------
    def whoami_async(self, force=False):
        if not force and not self.auto_external_checks.get():
            return

        def job():
            rc, out = run_cmd(["curl", "-s", "--max-time", "4", "https://1.1.1.1/cdn-cgi/trace"], timeout=6)
            info = parse_cf_trace(out)

            def show():
                self.nb.select(self.tab_log)
                if rc != 0 or not info:
                    self.log("Whoami: fehlgeschlagen (curl/Netz?).")
                    if out:
                        self.log(out)
                    return
                keys = ["ip", "loc", "colo", "warp", "tls", "http"]
                nice = " | ".join([f"{k.upper()}={info.get(k,'-')}" for k in keys])
                self.log(f"Whoami (Egress): {nice}")

            self.after(0, show)

        threading.Thread(target=job, daemon=True).start()

    # ---------- Connections (PID/program -> remote) ----------
    def connections_async(self):
        if not has_cmd("ss"):
            self.log("Verbindungen: 'ss' fehlt (iproute2).")
            return

        def job():
            rc, out = run_cmd(["sudo", "-n", "ss", "-H", "-tunap"], timeout=8)
            if rc != 0 or not out.strip():
                rc, out = run_cmd(["ss", "-H", "-tunap"], timeout=8)

            conns = parse_ss_lines(out)

            def fill():
                self.nb.select(self.tab_conn)
                self._conn_rows_cache = conns

                for item in self.conn_table.get_children():
                    self.conn_table.delete(item)

                for c in conns:
                    self.conn_table.insert(
                        "", "end",
                        values=(c["proto"], c["state"], c["local"], c["remote"], c["pid"], c["proc"])
                    )

                self.log(f"Verbindungen aktualisiert: {len(conns)} Zeilen (PID/Proc ggf. nur mit sudo sichtbar).")

            self.after(0, fill)

        threading.Thread(target=job, daemon=True).start()

    def arp_async(self):
        def job():
            rc, out = run_cmd(["arp", "-a"], timeout=8)
            if rc != 0 or not (out or "").strip():
                rc, out = run_cmd(["ip", "neigh"], timeout=8)

            def show():
                self.nb.select(self.tab_log)
                self.log("---- ARP Tabelle ----")
                self.log(out if out else "Keine Daten.")
            self.after(0, show)

        threading.Thread(target=job, daemon=True).start()

    def route_async(self):
        def job():
            _, out = run_cmd(["ip", "route"], timeout=6)

            def show():
                self.nb.select(self.tab_log)
                self.log("---- Routing Tabelle ----")
                self.log(out if out else "Keine Daten.")
            self.after(0, show)

        threading.Thread(target=job, daemon=True).start()

    def apply_conn_filter(self):
        q = (self.conn_filter.get() or "").strip().lower()
        rows = self._conn_rows_cache

        for item in self.conn_table.get_children():
            self.conn_table.delete(item)

        if not q:
            for c in rows:
                self.conn_table.insert("", "end", values=(c["proto"], c["state"], c["local"], c["remote"], c["pid"], c["proc"]))
            return

        for c in rows:
            blob = f"{c['proto']} {c['state']} {c['local']} {c['remote']} {c['pid']} {c['proc']}".lower()
            if q in blob:
                self.conn_table.insert("", "end", values=(c["proto"], c["state"], c["local"], c["remote"], c["pid"], c["proc"]))

    # ---------- DNS Status ----------
    def resolved_status_async(self):
        def job():
            lines = []

            _, out = run_cmd(["ls", "-l", "/etc/resolv.conf"], timeout=4)
            lines.append("---- /etc/resolv.conf (symlink) ----\n" + (out or "") + "\n")

            _, out = run_cmd(["cat", "/etc/resolv.conf"], timeout=4)
            lines.append("---- /etc/resolv.conf (content) ----\n" + (out or "") + "\n")

            if has_cmd("resolvectl"):
                rc, out = run_cmd(["systemctl", "is-active", "systemd-resolved"], timeout=4)
                lines.append(f"systemd-resolved: {out.strip() or 'unknown'} (rc={rc})\n")

                _, out = run_cmd(["resolvectl", "dns"], timeout=6)
                lines.append("---- resolvectl dns ----\n" + (out or "") + "\n")

                _, out = run_cmd(["resolvectl", "domain"], timeout=6)
                lines.append("---- resolvectl domain ----\n" + (out or "") + "\n")

                _, out = run_cmd(["resolvectl", "status"], timeout=10)
                lines.append("---- resolvectl status ----\n" + (out or "") + "\n")
            else:
                lines.append("Hinweis: resolvectl nicht vorhanden → systemd-resolved ist nicht aktiv/benutzt.\n")

            text = "\n".join(lines)

            def show():
                self.nb.select(self.tab_dns)
                self.dns_text.delete("1.0", "end")
                self.dns_text.insert("end", text)
                self.dns_text.see("1.0")
                self.log("DNS Status aktualisiert.")

            self.after(0, show)

        threading.Thread(target=job, daemon=True).start()

    # ---------- External IP/Country ----------
    def ip_country_async(self, force=False):
        if self.ip_country_running:
            return
        if not force and (time.time() - self.last_ip_ts) < 60:
            return
        self.ip_country_running = True

        def job():
            try:
                if not force and not self.auto_external_checks.get():
                    self.last_ip_ts = time.time()
                    return

                _, ip = run_cmd(["curl", "-s", "--max-time", "3", "ifconfig.me"], timeout=5)
                ip = (ip or "").strip()
                _, c = run_cmd(["curl", "-s", "--max-time", "3", "ipinfo.io/country"], timeout=5)
                c = (c or "").strip()

                if ip:
                    self.public_ip = ip
                if c:
                    self.country = c

                self.last_ip_ts = time.time()
                self.after(0, lambda: self.log(f"IP: {self.public_ip} | Land: {self.country}"))
            finally:
                self.ip_country_running = False

        threading.Thread(target=job, daemon=True).start()

    # ---------- Refresh ----------
    def refresh(self):
        inet = self.check_internet()
        vpn_profile = self.active_wg_profile()

        fw = self.check_ufw_active()
        ks = self.killswitch_is_on()

        self.update_dns_header()
        self.update_wg_rates()

        self.set_light(self.l_inet, "green" if inet else "red")
        self.set_light(self.l_vpn, "green" if vpn_profile else "gray")
        self.set_light(self.l_fw, "green" if fw else "red")
        self.set_light(self.l_ks, "green" if ks else "red")
        self.set_light(self.l_ipv6, "green" if not self.ipv6_is_disabled() else "red")

        choice = self.dns_choice.get()
        if DNS_PROFILES.get(choice) is None:
            self.set_light(self.l_dnscons, "gray")
        else:
            if self.last_dns_consistency_ok is True:
                self.set_light(self.l_dnscons, "green")
            elif self.last_dns_consistency_ok is False:
                self.set_light(self.l_dnscons, "red")
            else:
                self.set_light(self.l_dnscons, "gray")

        if DNS_PROFILES.get(choice) is not None:
            self.dns_consistency_check_async(force=False)

        self.ip_country_async(force=False)
        self.whoami_async(force=False)

        wg_if = self.get_wg_iface()
        default_if = self.get_default_iface() or "–"
        route_txt = f"über {wg_if}" if wg_if else f"über {default_if}"
        v6txt = "IPv6 AUS" if self.ipv6_is_disabled() else "IPv6 AN"

        parts = [
            "Internet OK" if inet else "Internet DOWN",
            f"VPN: {vpn_profile}" if vpn_profile else "VPN: aus",
            "UFW: aktiv" if fw else "UFW: aus",
            f"Killswitch: {'AN' if ks else 'AUS'}",
            v6txt,
            f"Traffic: {route_txt}",
            f"RX {human_rate(self.wg_rx_rate)} / TX {human_rate(self.wg_tx_rate)}",
            f"IP {self.public_ip} ({self.country})",
        ]
        self.status_text.config(text=" | ".join(parts))

    def auto_refresh(self):
        self.refresh()
        self.after(5000, self.auto_refresh)


if __name__ == "__main__":
    app = App()
    app.mainloop()
