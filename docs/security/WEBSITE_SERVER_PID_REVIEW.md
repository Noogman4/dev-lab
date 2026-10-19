# Website helper: shared PID file remediation

Date: 2026-10-19
Repository: Noogman4/dev-lab
Reviewed baseline: d4e40ad6262fe73a58ea0e930d41b12df874f66d (main)
Original scan revision: c6a6c5bfefd5189bfdab890aa608dea0c94078d9
Finding: Shared PID file can make the website stop helper signal an unrelated process
Severity: Low
Cloud occurrence: occ_d019e6335c4f454e677d973d

## Verification and scope

The vulnerability remains present in both shell helpers at the reviewed baseline.
The baseline stop script was executed with its PID-file path relocated into a
private test directory. A deliberately registered, synthetic sleeping child was
terminated with SIGTERM. No production process or shared host PID file was used.

This change affects the website development helpers only. NetMon application,
firewall, DNS, VPN, installed services and release tooling are outside its scope.
It is a local, uncommitted patch; no remote commit, push or Cloud closure was made.

## Implemented protection

- Both shell wrappers delegate lifecycle management to a standard-library Python
  helper. Existing browser opening, site URL and port override remain available.
- The global `/tmp/netmon_site_http_server.pid` and `.log` are never consulted,
  modified, migrated or deleted. A forged legacy PID therefore cannot select a
  target. If an old server still occupies the port, the new start fails safely;
  stopping that legacy server requires separate, verified manual action.
- Per-user and per-checkout runtime directories use mode 0700. Use a validated
  XDG_RUNTIME_DIR when set; otherwise use a validated root-owned mode-1777 `/tmp`
  with an exclusively created private subdirectory. No path component may be a
  symlink. Directory descriptors anchor later operations.
- State, lock and log files must be current-UID-owned regular files, mode 0600,
  with one link. O_NOFOLLOW/O_NONBLOCK reject unsafe entries without following
  symlinks, hanging on FIFOs or truncating targets. Unsafe existing entries fail
  closed. A persistent flock serializes complete start/stop operations.
- A bounded JSON state record requires an exact schema, positive bounded PID,
  valid port, expected repository, start time, boot ID and readiness descriptor.
  Complete state is fsynced and published without replacing an existing entry.
- Before signaling, pidfd_open pins the candidate process. The helper checks
  process UID, start time, cwd, executable and exact argv against the expected
  website server. fdinfo maps that handle to the mounted procfs namespace, so
  container PID/procfs namespace differences are handled explicitly.
- SIGTERM is sent through signal.pidfd_send_signal on the checked handle. PID
  reuse cannot redirect the signal. Exited processes are handled safely; there
  is no numeric-kill fallback for registered processes.
- The child acknowledges readiness through a private inherited pipe only after
  binding its own loopback HTTP listener. An unrelated listener on the requested
  port cannot satisfy startup. The server binds only 127.0.0.1.
- Launch/publication failure terminates and reaps only the helper's own unreaped
  direct child, never a PID loaded from state.

## Validation

Command: `python3 -m pytest -q tests/test_netmon_site_server_security.py`
Result: **70 passed, 3 skipped** (10.60 seconds).

Coverage includes the baseline attack, survival of a registered unrelated child,
invalid PIDs/metadata, stale start time and boot ID, wrong cwd/argv, PID-handle
signaling, exit between validation and signaling, unsafe files and directories,
symlinks/hardlinks/FIFOs, publication failures, bounded state, occupied ports,
concurrent starts/stops, private /tmp fallback, browser-wrapper URL and actual
synthetic HTTP content, restart, and failure before launch when pidfds are absent.

Three real foreign-owner file cases were skipped: this container maps only UID
0 and rejects chown to a second UID (EINVAL). Owner validation was additionally
exercised with synthetic stat metadata. A real two-UID end-to-end attack was not
run. Bubblewrap namespaces and Unix-socket binding are unavailable here; tests
used private temporary directories and synthetic processes/loopback HTTP inside
the execution container. No external requests or real browser were used.

Ruff, Black --check, Python compilation, Bash syntax and git diff --check passed.
No full NetMon application suite or paid Cloud scan was run for this helper-only
change. These results establish the tested remediation, not a general audit of
NetMon or a claim that every possible runtime failure was tested.

## Compatibility and security boundary

Requires Linux with pidfd_open/pidfd_send_signal, accessible procfs and Python
3.11+ as already required by this repository. Missing capabilities fail closed.
The scripts should run as the normal desktop user. A malicious process with the
same UID or root already has authority over that user's files/processes; this
change addresses the reported different-UID local attacker and PID reuse.

Next: apply the patch, rerun its tests on the target desktop, then commit/push
through the normal VS workflow. Formal Cloud closure is a separate explicit
operation after the published fix revision is verified.

## Local application and Bubblewrap validation

The preceding 70-pass/3-skip result describes the supplied patch author's
execution container. It is not the local Bubblewrap result. On 2026-10-19,
the patch was applied locally on the same baseline
`d4e40ad6262fe73a58ea0e930d41b12df874f66d`. The three production files are
unchanged from the supplied patch. Only the test fixture and this report were
adjusted during local validation.

The unchanged Bubblewrap probe passed: non-root UID, NoNewPrivs, read-only
repository, private PID/network namespaces without host routes, and no host
home, WireGuard/NetworkManager configuration or service sockets. All pytest
runs used `tests/run_isolated_suite.py` and the unchanged Host-Access-Guard.
No system service, external network, real browser or host process was used.
Synthetic child-process termination remained inside the private PID namespace.

Two environment differences were handled without relaxing production checks:

- The first run stopped with 1 passed and 1 failed test: the shell wrapper used
  system Python while direct calls used the test virtual environment. Exact
  process-command identity correctly rejected that mismatch. The fixture now
  supplies a local `python3` shim that execs `sys.executable`, so both test
  entrypoints use identical interpreter argv. All original assertions remain.
  The previously failing lifecycle test then passed in isolation.
- The next run reached 68 passed, 3 skipped and 1 failed: Bubblewrap's synthetic
  `/tmp` is UID 1000, mode 0755. The production fallback correctly requires
  root-owned mode 1777 and rejected it. The real `/tmp` fallback lifecycle test
  now explicitly checks that prerequisite and skips when unavailable; its
  existing assertions still execute when the prerequisite holds. The check was
  not mocked away, no host `/tmp` mount was added, and no permissions changed.

Final local results:

| Selection | Result | Local artifact directory under `/tmp/user/1000/` |
| --- | --- | --- |
| Website PID tests | 69 passed, 4 skipped, 0 failures | `netmon-isolation-zz5ao2ce` |
| Website plus diagnostics, support bundle and guard | 184 passed, 5 skipped, 0 failures | `netmon-isolation-j5pftan8` |

The combined run took 8.08 seconds. Its 189 cases comprise 73 website cases,
16 diagnostic-collector cases, 32 support security cases, 3 support cases,
3 core diagnostic cases, 41 application diagnostic cases and 21 guard cases.
The 73 website cases are included in the combined count, not additional tests.
Each artifact directory contains `junit.xml`; these are local artifacts, not
repository files. No unpublished About test is part of these selections.

Four website cases remain **unvalidated** end to end: three real foreign-owner
file cases (no second UID/chown permission) and the real root-owned `/tmp`
fallback lifecycle. Synthetic foreign-owner metadata checks do pass. The fifth
combined skip is the diagnostic collector's existing real-chown case.

Reproduction requires the existing test dependencies and Git history containing
the baseline commit, which the original-attack test reads with `git show`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests/test_netmon_site_server_security.py \
  tests/test_collect_netmon_diagnostics_security.py \
  tests/test_support_bundle_security.py tests/test_support_bundle.py \
  tests/test_core_diagnostics.py tests/test_netmon_diagnostics.py \
  tests/test_host_access_guard.py
```

ShellCheck, Ruff, Black, Bash/Python syntax and `git diff --check` passed locally.
No full project suite, Cloud scan or Cloud finding-state change was performed.
Start/stop operations must use a consistent interpreter invocation; switching
Python entrypoints can intentionally fail the exact argv identity check.
The same-UID/root boundary described above remains unchanged, as does the
separate, partially mitigated L-04 authorization finding. Local About work,
the test starter and the guard are preserved. `secure-browser/` was not read or
changed and remained hidden in the test namespace. No commit, push, deployment
or host configuration change was performed for this patch.
