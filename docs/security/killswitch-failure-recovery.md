# Kill-switch failure recovery: defensive verification and correction

Date: 2026-10-19
Repository: Noogman4/dev-lab
Reviewed main HEAD: 71ed081b77e26af8853d340e777009f027251082
Cloud finding: csf_2cab4424ec90ad471a265646 (Medium)
Occurrence: occ_5ae30c7f1f027f978289f9d1

## Verified defect

The original production recovery function was loaded from the reviewed commit
and executed against a synthetic state initially configured with deny incoming
and deny outgoing. Its actual commands changed outgoing to allow. The finding
is independently reproduced; no real UFW commands or host changes were used.

## Correction and resulting behavior

This change deliberately uses the finding's restrictive fallback option. It is
NOT an exact rollback implementation. The existing controller cannot restore
arbitrary prior UFW state reliably without a separate transaction mechanism.

* Failure recovery never issues `default allow outgoing`.
* Recovery attempts to insert unrestricted DENY OUT and DENY IN rules at position
  one, set both defaults to deny, and enable UFW. The inserted rules protect
  against ALLOW rules left by a partially completed activation.
* Recovery checks active status and leading unconditional deny rules for both
  IPv4 and IPv6. Unknown rule policies, missing families, interface-limited deny
  rules, and preceding allows prevent a successful recovery claim.
* Every parsed recovery rule must have an explicit IN or OUT direction. Missing
  or unsupported directions prevent verification, even after the expected denies.
* Every recovery command's return code is checked. An exception or failure does
  not prevent the remaining restrictions from being attempted. Failed recovery
  is explicitly reported as protection NOT guaranteed.
* The app marks manual recovery as required and logs that the prior configuration
  has not been restored. Emergency rules remain; they are not silently removed.
* Cleanup failures now stop activation. Activation stops at the first failed
  apply command. Verification and recovery run inside the same UFW lock as apply.
* Exceptions during mutation also enter recovery before releasing that lock.
  An unreadable initial status aborts without starting any mutations.
* The ordinary enabled/disabled verifier rejects unconditional global blocking
  rules, so emergency state is not presented as normal working VPN connectivity.
* The shared App recovery entry point returns the verification result. Its other
  callers also receive restrictive recovery rather than the old permissive reset.

## Validation

Command:

    python -m pytest tests/test_killswitch_failure_recovery.py tests/test_netmon_killswitch.py tests/test_firewall_controller.py tests/test_ufw_locale.py tests/test_netmon_vpn_slots.py -q

Result: **238 passed**, including **100 new tests**. The new stateful fake tracks
ordered rules separately for both address families and checks resulting state,
not just command emission. It covers each activation mutation (including rule
cleanup and initially inactive UFW), runner exceptions and nonzero exits, both
command dispatch paths, final status failure, all emergency-command failures,
strict recovery verification, and one continuous lock acquisition through error
handling. Existing App-level kill-switch and VPN-slot tests also pass.

Black check, Python compilation, git diff --check, and Ruff fatal-error checks
passed. The new test file passes full Ruff. The production controller still has
pre-existing general Ruff warnings; comparison with the original file found no
increase by diagnostic code (88 original warnings, 85 after this change).

## Limits and operational consequences

No live firewall or kernel packet-filter test was performed. Verification checks
UFW's displayed user rules, not conntrack, existing established connections,
forwarded traffic, or custom before.rules. No claim of universal packet isolation
is made. Missing IPv6 rules (including hosts configured without UFW IPv6 support)
result in an unverified recovery warning rather than assumed protection.

The emergency rules can block new SSH, VPN, and other connections. Manual UFW
inspection and deliberate recovery are required after failure. Previously
successful rules may remain in storage, behind the emergency denies; deleted
pre-existing rules are not recreated. Exact pre-state equality is not provided.
If UFW itself rejects recovery commands, the app reports that protection cannot
be guaranteed; software cannot promise recovery from unavailable privileges or
a failing firewall backend.

No automatic commit or push was made, in accordance with AGENTS.md. No Cloud
finding status was changed. The fix must be applied, reviewed, pushed and checked
against the resulting commit before formal closure.

## Local application and Bubblewrap review

The preceding 238-pass result and Ruff warning counts describe the supplied
patch report. The patch was applied locally on 2026-10-19 to the reviewed
`71ed081b77e26af8853d340e777009f027251082` baseline. The unchanged Bubblewrap
probe passed: non-root UID, NoNewPrivs, read-only repository, private PID/network
namespaces without host routes, and no host home, WireGuard/NetworkManager
configuration or service sockets. All pytest runs below used the existing
`tests/run_isolated_suite.py` and unchanged Host-Access-Guard. UFW, sudo and
NetworkManager operations were simulated; no live firewall changes were made.

The supplied 100 new tests passed locally. The original five test files then
passed together with 21 guard tests: **259 passed, 0 failures or skips**.
Subsequent code review identified an additional synchronization defect in the
supplied patch: three failure branches called `refresh_safe()` while still
holding the non-reentrant `ufw_lock`. On the GUI main thread, the real
`App.refresh_safe()` calls `refresh()` synchronously; its killswitch status query
acquires the same lock. A UI refresh could therefore hang after recovery.

A deterministic regression reproduced this path using the real
`App.refresh_safe()` dispatch, the real `killswitch_is_on()` lock acquisition,
synthetic status data and a lock that fails immediately on reentry rather than
hanging the test. The first case failed before the local correction
(`netmon-isolation-u2p34sz0`). Production recovery and verification remain under
the same lock; only the three failure-path UI refreshes are now deferred until
the lock has been released. All three regression cases (apply-command failure,
verification-read failure and rule-verification failure) then passed.

One additional baseline regression loads only the original recovery function
from the exact reviewed Git revision and executes it against the stateful UFW
fake. It confirms that the old implementation changes deny outgoing to allow.
No baseline module top-level code or real privileged command is executed.
The 100 supplied security tests and their assertions remain unchanged.

Final local selection:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests/test_killswitch_failure_recovery.py \
  tests/test_netmon_killswitch.py tests/test_firewall_controller.py \
  tests/test_ufw_locale.py tests/test_netmon_vpn_slots.py \
  tests/test_host_access_guard.py
```

Result: **263 passed, 0 failures, 0 errors, 0 skipped in 2.88 seconds**.
JUnit artifact: `/tmp/user/1000/netmon-isolation-agxqn_ss/junit.xml` (local,
not committed). The selection comprises 104 recovery, 47 existing killswitch,
16 firewall-controller, 3 UFW-locale, 72 VPN-slot and 21 guard cases. The earlier
runs are subsets, not additional unique tests. No unpublished About test is
included. The baseline regression requires Git history containing the reviewed
commit; a source-only export without that history cannot run that case.

Full Ruff checks with the local project configuration report no findings for
the three affected Python files; the pre-change snapshots of `app.py` and the
controller also report none. Thus the supplied report's 88/85 warning counts
are not local results. Black and Python syntax checks passed for all three
Python files, as did `git diff --check`. No lint exclusions, guard changes or
new dependencies were introduced. No shell file was changed.

The scope remains four files: the App recovery bridge, firewall controller,
new recovery tests and this report. The existing About diff is fully preserved:
reversing only the supplied App recovery hunk in a temporary copy restores the
pre-application `app.py` bytes exactly. Other About files, L-01/F-01/L-04 import
code, guard and isolation starter are hash-identical to their saved snapshots.
`secure-browser/` was neither read nor modified and remained hidden in the
test namespace. HEAD and index are unchanged; no commit or push was performed.

No full application suite, live packet-filter test, Cloud scan or formal Cloud
closure was performed. The emergency deny rules require explicit manual
recovery and may block new SSH/VPN connections; arbitrary prior UFW state,
conntrack, forwarded traffic and custom before.rules remain outside the
verified guarantee. The separate L-04 same-UID authorization blocker remains
open. No host network operation, installation, deployment or system change was
performed.

## Independent-review follow-up: ambiguous rule directions

An independent, read-only local review reproduced the original outgoing-policy
weakening and reran the previous selection: 263 passed. Its separate temporary
audit yielded 201 passed and one failed security expectation. The failure was
in the recovery verifier: a rule such as `Anywhere ALLOW Anywhere` was parsed
with an empty direction, stored under an unused key and ignored when checking
the four IPv4/IPv6 IN/OUT keys. Following unconditional deny rules could thus
produce a positive verification result despite the ambiguous preceding line.
This established a verification defect on synthetic status data, not an actual
packet-filter bypass or proof that a supported UFW version emits that format.

After explicit authorization, the local correction adds only a two-line check
in `_killswitch_failure_is_closed()`: every parsed rule must have direction
`IN` or `OUT`; otherwise verification returns false. The shared parser, ordinary
firewall displays, command execution, locking and the App bridge are unchanged
by this follow-up. A valid, explicit IN/OUT output still passes. Unsupported
directions, including FWD, and formats omitting directions conservatively make
recovery unverified. They do not prevent the restrictive commands from being
attempted or cause an automatic permissive fallback.

Forty permanent cases were added to `tests/test_killswitch_failure_recovery.py`:
36 verifier cases cover ALLOW/DENY/REJECT, missing/FWD/unknown direction, both
families and placement before/after valid denies. Four full-recovery cases
confirm that even five successful command results cannot produce a protection
claim when the returned status is ambiguous. They require false return,
manual-recovery state and the explicit protection-not-guaranteed warning.
Existing tests and assertions were preserved.

The new regression failed before the correction
(`netmon-isolation-k3_7lcao`), then all 40 cases passed
(`netmon-isolation-042bc80g`). The unchanged Bubblewrap probe passed before
these runs (`netmon-isolation-gi0gpqxq`). All final runs retained the existing
Host-Access-Guard, synthetic UFW and isolated PID/network namespaces:

| Selection | Result | Local artifact under `/tmp/user/1000/` |
| --- | --- | --- |
| Repository selection using the six-file command above | 303 passed, 0 failures/errors/skips, 2.91 seconds | `netmon-isolation-shl15f2v/junit.xml` |
| Unchanged independent audit in its temporary copy | 202 passed, 0 failures/errors/skips, 0.98 seconds | `netmon-isolation-b36pn4nw/junit.xml` |

The 303 repository cases comprise 144 recovery cases plus the previously
listed 159 existing killswitch, firewall, locale, VPN-slot and guard cases.
They are reproducible using the six-file command in the preceding section.
The 202 supplemental audit cases, including 192 combinations of multiple
emergency-command errors/partial family writes across both dispatch paths,
are local-only evidence: their source is
`/tmp/user/1000/netmon-killswitch-independent-ezk_5l2r/checkout/tests/test_independent_recovery_audit.py`.
That temporary audit source and its JUnit outputs are not repository files and
must not be represented as a published test selection. Earlier runs and the
40-case subset are not additional unique repository cases.

Ruff, Black, Python syntax and `git diff --check` passed. Only the controller,
recovery test file and this document changed during this follow-up. The App,
About work, import security code, guard, isolation starter, HEAD and index
remain unchanged. No full suite, live firewall or privileged operation, host
network access, dependency installation, commit, push or deployment occurred.
`secure-browser/` remains unread and unchanged.

The verification blocker is locally corrected. Recovery is still best effort
when UFW rejects commands: partial activation permissions can remain, and a
failed emergency command must still yield false and the warning. There is no
exact pre-state rollback or claim of universal packet isolation. UI callback
errors can still propagate after recovery; the independent tests confirmed
that the tested callback-error path released the lock and retained emergency
denies. The limits concerning conntrack, forwarded traffic, before.rules and
the separate L-04 authorization issue remain unchanged. Formal Cloud closure
and publication are separate actions, not performed by this local correction.
