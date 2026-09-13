# Harmonize project handoff

Updated 2026-09-13 after acceptance of Milestone 7. `PROJECT.md`, milestone
documents, tests, and Git history remain the authoritative specification.

## Accepted state

- Milestones 0 through 7 are complete and accepted. Do not reopen them without
  an explicit owner request.
- Accepted Milestone 7 implementation: `9842b8c` (`Deploy Harmonize as a
  systemd appliance`). The Homebridge roadmap definition was added by
  `e61ed64`.
- This handoff was created on `modernize` immediately after `e61ed64`, with the
  branch clean and exactly synchronized to `origin/modernize`. The commit that
  contains this file is the next documentation-only commit and is the current
  handoff point.
- All 97 offline tests and `systemd-analyze verify` passed for Milestone 7.
- Milestone 7 rollback tooling and instructions exist. The owner accepted the
  milestone with the uninstall/reinstall execution intentionally skipped.
- Milestone 8 has not begun. No Homebridge adapter or permission change has
  been implemented.

## Installed appliance state

At handoff, `harmonize.service` is loaded, enabled, active, and running. It
starts ready in IDLE and waits for an explicit ON request. The unit and its
operator/rollback instructions are in `deploy/harmonize.service` and
`docs/milestone-7-systemd.md`.

The service runs as the locked account `harmonize` (UID 997, primary GID 985,
shell `/usr/sbin/nologin`) with only the supplementary `video` group. Relevant
paths are:

- root-owned application and virtual environment under `/opt/harmonize`
- configuration under `/etc/harmonize` (`0750 root:harmonize`)
- private runtime directory `/run/harmonize` (`0700 harmonize:harmonize`)
- private state directory `/var/lib/harmonize` (`0700 harmonize:harmonize`)
- stable WARKKY capture path configured under `/dev/v4l/by-id`

The local control provider accepts `ON`, `OFF`, and `STATUS` through
`/run/harmonize/harmonize.sock`. The socket is owner-only (`0600`) inside the
private runtime directory. `tools/harmonize_control.py` is the existing client.
The desired-state/provider boundary remains independent of any automation
system. Explicit OFF and service stop turn every light in exactly `TV area`
off; exceptional cleanup may restore pre-session state as documented.

## Milestone 8 boundary

Milestone 8 is **Homebridge Control Adapter**, defined in `PROJECT.md`. The
owner will create or use a Homebridge dummy switch. Homebridge already exports
that switch to HomeKit, so HomeKit integration, HomeKit state management, and
HomeKit-specific logic are entirely out of scope.

The preferred design is the smallest reliable local adapter, such as a
root-owned `harmonizectl` command that maps fixed ON/OFF/STATUS operations to
the existing Unix socket. Do not add an HTTP server, network listener, or
Homebridge logic to Harmonize. STATUS may provide a simple machine-readable
result if the installed dummy-switch mechanism can use it.

Homebridge currently cannot reach the socket directly because both the socket
and its parent directory are private to `harmonize`. Milestone 8 must first
identify the actual Homebridge service account and supported dummy-switch
command hooks, then choose the narrowest permission boundary. Do not casually
add Homebridge to the `harmonize` group or grant general sudo, shell, systemd,
configuration, state, or credential access. A fixed, root-owned adapter plus a
tightly constrained non-interactive invocation is preferred over broad access;
the implementation choice still requires review and offline tests.

Live acceptance will toggle the Homebridge dummy switch: ON must reach
STREAMING with both `TV area` lights following video, and OFF must reach IDLE
with both lights powered off. Setup, diagnostics, status behavior if used,
permission removal, and rollback must be documented.

## Safety and scope

- `client.json` contains Hue credentials. Never display, log, copy into
  diagnostics, or commit it. The repository file is ignored and mode `0600`;
  the installed credential is also private. Validate metadata only.
- Resolve and control only the configured Entertainment area named exactly
  `TV area`. Preserve bounded cleanup and leave Entertainment inactive after
  every live test.
- Do not reset, clean, stash, discard, or overwrite user work during takeover.
- Docker, AirPrint, and host CUPS are out of scope. Do not inspect, test,
  validate, modify, or report on them for Milestone 8.
- Do not begin Milestone 9 visual-quality work.

## What the next agent must do first

Before making any change, read this file, `PROJECT.md`,
`docs/milestone-7-systemd.md`, `docs/milestone-5-state-machine.md`, and the
relevant tests and Git history. Verify that `modernize` is clean and
synchronized with `origin/modernize`, and confirm the Harmonize service state
without exposing credentials. Report the exact takeover state and a smallest
safe adapter/permission proposal to the owner before editing.

Only after explicit authorization to start Milestone 8 should the next agent
create `m8-homebridge-adapter` from the accepted `modernize` head and inspect
the Homebridge service identity and dummy-switch command capabilities. Stop at
the Milestone 8 boundary for review; never proceed automatically to Milestone
9.
