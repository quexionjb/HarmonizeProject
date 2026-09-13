# Milestone 6 pre-live handoff

Date: 2026-09-13

## Exact checkpoint

- Branch: `m6-light-state`
- Accepted base: `66d5495c76ae3b9110226dcae03181332496964d`
  (`modernize`, accepted Milestone 5)
- Offline implementation commit: `d88e7b7` (`feat: checkpoint Milestone 6
  light state handling`)
- Current checkpoint: `origin/m6-light-state` at the commit containing this
  document; Milestone 6 is **in progress and awaiting live visual validation**.
- No Milestone 7 work has begun.
- The intended committed tree contains no credential file or secret value.

At handoff creation, no Harmonize or OpenSSL DTLS process was running, the
control socket was absent, and no pending light-state journal existed. The
ignored health snapshot remained at `run/harmonize-health.json`. The ignored
`client.json` remained mode `0600`; do not read, print, edit, or commit it.

## Completed implementation

The checkpoint adds:

- exact `light_services` mapping from the configured Entertainment area;
- Hue v2 read and update operations for individual light resources;
- static state capture for on/off, brightness, XY color, and valid color
  temperature;
- refusal to start restore-mode Ambilight when a light has an active dynamic
  scene, timed effect, effect, or unsupported mode that cannot be replayed
  safely;
- verified `restore` and `off` post-stream modes with bounded per-light retries;
- state capture immediately before Hue Entertainment start and state apply only
  after a successful Entertainment stop;
- an atomic, owner-only, non-secret session journal with session/area/light
  membership guards;
- stale crash journals that are never applied automatically and block another
  ON cycle until explicitly resolved;
- explicit recovery commands in `tools/harmonize_light_state.py`: `inspect`,
  `restore`, `off`, and `discard`, with exact-area confirmation and a separate
  stale override;
- supervisor behavior that leaves cleanup failures visible in `ERROR` until a
  new OFF command acknowledges them; and
- startup logging for pending or invalid recovery journals.

The full offline suite passed: **87 tests**. New coverage includes representative
on/off, brightness, XY and color-temperature round trips, off mode, journal mode
and symlink checks, stale and mismatched sessions, bounded partial failures,
uncertain Entertainment stop, cleanup-error visibility, Hue area membership,
and recovery-tool parsing. Existing Milestone 3 through 5 tests still pass.

Read-only live discovery established that `TV area` has two light services,
`TV Right` and `TV Left`, both Hue Play lights. Their bridge payload supports
the static fields above and showed no active dynamic/effect mode. A read-only
preflight captured both into `run/harmonize-light-state.json`, verified the file
as mode `0600`, inspected it successfully, and explicitly discarded it. That
file is currently absent. No Entertainment session or light change was made in
Milestone 6.

## Files and local state

- Normal recovery journal:
  `run/harmonize-light-state.json` (ignored, mode `0600` when present)
- Daemon health:
  `run/harmonize-health.json` (ignored; may contain an old IDLE snapshot)
- Local command socket:
  `run/harmonize.sock` (ignored; absent when the daemon is stopped)
- Hue credentials:
  `client.json` (ignored, mode `0600`; never include its contents in output)
- No original-state live-test backup has been created yet.
- No temporary live-test TOML file has been created yet.

Do not delete or discard a future pending journal merely to get a clean Git
status. Files under `run/` and `*.local.toml` are intentionally ignored.

## Pending live visual validation

The user has **not yet confirmed readiness** after being shown the procedure.
The next agent must not change Hue state until the user explicitly says they
are ready to watch.

After confirmation, use only exact `TV area` and perform these stages:

1. Re-run the 87-test suite and read-only checks. Confirm the area is inactive,
   no Harmonize/DTLS process is running, and the normal journal is absent.
2. Immediately capture the current original state into a separate owner-only
   backup such as `run/m6-original-baseline.json`. Also prepare an ignored local
   recovery config whose `light_state.journal_file` points to that backup, so
   `tools/harmonize_light_state.py` can restore it if the session is interrupted.
3. Set a controlled restore baseline through Hue v2 and verify it through GET:
   `TV Right` on at moderate brightness with a clearly visible blue/cyan XY
   color; `TV Left` off with a stored moderate brightness and color temperature.
4. Start the restore-mode daemon, send ON, STATUS, then OFF. Verify through Hue
   GET that right returns to the exact static color/brightness and left returns
   off with its stored brightness/temperature. Verify Entertainment inactive
   and the normal journal removed.
5. Repeat restore with `--inject-failure after_dtls_ready` and a local config
   setting `control.recovery_attempts = 0`. Verify cleanup restores the same
   baseline, leaves Entertainment inactive, and removes the normal journal.
6. Set both lights to distinct visible static states, use an ignored local
   config with `ambilight.post_stream_behavior = "off"`, run ON/STATUS/OFF, and
   verify both light resources report off and Entertainment reports inactive.
7. Restore the original state from the separate baseline backup, verify every
   captured field through Hue GET, then remove that backup through the guarded
   recovery path. Stop the daemon and verify no journal, socket, Harmonize, or
   DTLS process remains.

Ask the user to report these observations:

- Before restore testing: right is steady blue/cyan at moderate brightness and
  left is off.
- During ON: both lights visibly follow the captured video.
- After restore OFF: right returns to the same steady blue/cyan appearance and
  left returns off.
- After the injected failure: the same controlled pre-stream appearance returns.
- After off-mode OFF: both lights are off.
- After final recovery: the original pre-test appearance returns.

The API results establish resource values; the user's observation is required
to establish physical appearance and absence of an unexpected flash or segment
behavior.

## Cleanup and recovery requirements

On any failure or interruption:

1. Stop only the exact configured area with
   `tools/stop_entertainment.py --config <test-config>`.
2. Query Hue read-only and require `TV area` status `inactive`.
3. If `run/harmonize-light-state.json` exists, inspect it first. Use guarded
   `restore` with `--confirm-area "TV area"`; add `--allow-stale` only after the
   user confirms the saved state is still appropriate. Do not discard an
   unresolved journal by default.
4. Restore the separate original baseline using its prepared recovery config
   and the same exact-area guard.
5. Re-query both light resources and Entertainment status. If any restore is
   partial, retain the journal, report the exact light and field, and do not
   claim Milestone 6 acceptance.
6. Stop the daemon, verify the socket is absent, and verify no Harmonize or DTLS
   process remains.

External light changes during an active Ambilight session cannot be reliably
distinguished from the current session through ordinary Hue GET responses.
The defined safe policy is to send Ambilight OFF before changing these lights
from another app. Automatic restoration is limited to the in-memory session
that captured the journal; crash leftovers require explicit human recovery.

## First action for the next agent

Read this file and `PROJECT.md`, then run only repository/status and the full
offline test suite. Report that the branch is the pre-live checkpoint and ask
the user to confirm they are ready to observe the six visual checkpoints above.
Do not contact Hue with a state-changing request before that confirmation.
