# Harmonize Modernization Project

## Objective

Turn Harmonize into an appliance-like Ambilight service on this Raspberry Pi 5 running Ubuntu. The service should run unattended, detect whether the HDMI/video source is worth illuminating, start and stop Hue Entertainment streaming automatically, and restore the affected lights or turn them off afterward. It must coexist safely with the production airprint Docker print service and the Pi's other Docker workloads; host-level CUPS is intentionally inactive and out of scope.

This roadmap is the persistent tracker for that work. Implementation stops at every milestone boundary for review and explicit authorization.

## Current Baseline

- Hardware: Raspberry Pi 5, 64-bit ARM.
- Operating system: Ubuntu with Linux 6.8.0-1064-raspi observed during initial discovery.
- Python: 3.12.3 in both the system interpreter and /home/pi/harmonize_env.
- Computer vision: OpenCV 4.10.0 with GStreamer 1.24.2, FFmpeg, and V4L2 support; NumPy 1.26.4.
- Capture: /dev/video0 and /dev/video1 exist, along with Pi codec devices. User pi belongs to the video group. Capture behavior under HDMI state changes is not yet characterized.
- Harmonize: upstream v2.4.2 at commit 51b4f52; no Harmonize process or systemd service was running during discovery.
- Hue: client.json exists only as a local ignored file in the current checkout. The current file is not tracked and its content hash does not match historical client.json blobs. Older upstream history did track files at that path before removing it, so history must never be treated as a safe place for credentials.
- Docker: docker.service was active and enabled at the Milestone 0 baseline. The existing airprint container is the production print service and printing is working normally. User pi cannot read the Docker API socket, so container health and other workloads require an authorized read-only validation method.
- Host CUPS: cups.service is inactive and disabled by design because printing is provided by airprint. Do not install, enable, start, reconfigure, or otherwise modify host-level CUPS.
- Deployment: the application currently depends on an interactive terminal or screen session and uses no native service unit.
- Architecture: harmonize.py combines discovery, Hue API access, capture, analysis, HueStream encoding, DTLS transport, threading, and interactive lifecycle control in one process.

## Project Principles

- Reliability before new features.
- Preserve a known-working state at every milestone.
- Make small, reviewable commits.
- Do not mix unrelated milestones in one change.
- Do not disrupt CUPS or Docker: preserve the airprint container and other Docker workloads, and leave host-level CUPS untouched.
- Do not expose Hue credentials or other secrets.
- Prefer measurement and testing over assumptions about the hardware.
- Preserve working Harmonize behavior before trying to improve its visual output.
- Every milestone must have a clear rollback point.
- Stop at milestone boundaries for review before proceeding.

## Repository and Branch Strategy

- origin is the working fork: https://github.com/quexionjb/HarmonizeProject.git
- upstream is the source project: https://github.com/MCPCapital/HarmonizeProject.git
- Local master tracks origin/master and remains the clean fork baseline.
- modernize is the integration branch for this roadmap.
- Use focused topic branches such as m1-source-detection when a milestone benefits from isolated experiments or review.
- Merge or fast-forward only reviewed milestone work into modernize.
- Record the accepted commit SHA at each boundary and optionally add an annotated milestone tag.
- Pull upstream changes deliberately: fetch upstream, inspect the diff, test on a topic branch, and merge only after confirming that appliance behavior and local safety are preserved.
- Never commit client.json, environment files, private keys, local credential configuration, logs, PID files, sockets, virtual environments, or Python caches.

## Rollback Philosophy

Each milestone begins from a known commit and ends at a separately reviewable commit. Before installing files outside the repository, capture the current file, package, service, permissions, and workload state needed to reverse the operation. Repository rollback should normally mean checking out the previous accepted commit or reverting the milestone commit. System rollback must restore prior service units and configuration, reload systemd when needed, verify airprint and other Docker workloads against their recorded baselines, and leave host-level CUPS untouched. Avoid irreversible migrations; credential and configuration changes require a documented recovery path.

# Milestones

## Milestone 0 — Repository and Safety Baseline

### Objective

Create a safe Git foundation and a Pi-specific modernization roadmap without changing Harmonize runtime behavior.

### Why it matters

Credentials and unrelated appliance workloads must be protected before experiments or refactoring begin. A recorded upstream baseline and small commits provide a dependable recovery point.

### Planned work

- [x] Verify origin, upstream, and master tracking.
- [x] Confirm the current local client.json is untracked and compare it safely with historical blobs.
- [x] Expand .gitignore for credentials, secret-bearing local configuration, virtual environments, caches, logs, and runtime files.
- [x] Create modernize from upstream v2.4.2 commit 51b4f52.
- [x] Commit repository housekeeping separately.
- [x] Record the observed Pi, capture, Python, OpenCV, airprint/Docker, and intentionally inactive host-CUPS baseline.
- [x] Create and commit this roadmap.
- [x] Push modernize to origin and record whether Git authentication permits it.

### Acceptance criteria

- [x] client.json remains present locally, unchanged, untracked, and ignored.
- [x] Local master tracks origin/master.
- [x] modernize contains a focused repository-housekeeping commit.
- [x] PROJECT.md contains objectives, work, acceptance criteria, risks, and status for every milestone.
- [x] No capture experiment, Hue request, service installation, host-CUPS change, or Docker change has occurred.
- [x] The push outcome is reported at the milestone review.

### Risks/unknowns

- Upstream history previously contained client.json files, so historical credentials may have existed even though the current credential is distinct.
- GitHub connector access and local Git command authentication are separate; local GitHub CLI authentication is now configured and modernize tracks origin/modernize.
- User pi cannot access the Docker socket directly, so airprint health and other workload details require an authorized read-only validation method.
- Host CUPS is intentionally inactive and disabled; changing that state would conflict with the production airprint architecture.

### Status

Complete. The baseline commits are on origin/modernize.

## Milestone 1 — Determine Reliable TV/Source Activity Detection

### Objective

Measure how the installed USB capture path behaves and select the simplest reliable signal meaning there is video worth running Ambilight for.

### Why it matters

Automatic control is only trustworthy if active and inactive source states can be distinguished without flapping, false starts, or assumptions about HDMI behavior.

### Planned work

- [x] Record USB identity, driver, V4L2 capabilities, supported formats, resolutions, and frame rates for the capture device associated with /dev/video0.
- [x] Measure frame availability, read latency, timestamps, resolution, and device state while the HDMI source is actively playing.
- [x] Repeat measurements with the HDMI source powered off or in standby.
- [ ] Repeat with the TV off while the HDMI source remains active.
- [ ] Measure active-to-inactive and inactive-to-active transitions, including timing and transient errors.
- [ ] Determine whether device state, frame delivery, timing, resolution changes, or frame contents provide the most reliable signal.
- [x] Analyze frame contents only if lower-level signals are insufficient.
- [x] Check installed HDMI-CEC devices, kernel support, and user-space tools without assuming CEC is required.
- [x] Build a repeatable, read-only capture diagnostic and record results.
- [x] Avoid Hue bridge contact or control unless a compelling need is explained and approved first.

### Acceptance criteria

- [ ] All four required HDMI/TV conditions have repeatable observations.
- [ ] Transition timing and false-positive/false-negative behavior are documented.
- [ ] The chosen detection signal has a stated sampling interval, debounce proposal, and failure semantics.
- [ ] CEC is classified as available/unavailable and useful/unnecessary.
- [ ] No Hue state was changed.
- [ ] The accepted results and rollback commit are recorded before Milestone 2.

### Risks/unknowns

- The capture adapter may continue emitting frozen, black, blue, or test-pattern frames without HDMI input.
- TV power may not affect the splitter/capture path when the source remains active.
- /dev/video numbering may change after reboot or reconnect.
- OpenCV, GStreamer, and direct V4L2 reads may report failures differently.
- CEC may not pass through the splitter or USB capture adapter.

### Status

In progress. Hardware inventory and the repeatable non-recording probe are complete; controlled physical-state and transition measurements remain.

## Milestone 2 — Establish Configuration and Dependency Boundaries

### Objective

Create a reproducible Python environment and a validated configuration layer while safely preserving existing Hue credentials.

### Why it matters

The current manually assembled environment and script-level options are difficult to reproduce, audit, deploy, and recover.

### Planned work

- [ ] Inventory imports and system dependencies, including OpenCV/GStreamer and the OpenSSL DTLS requirement.
- [ ] Choose and document a reproducible Python dependency specification compatible with aarch64 Ubuntu and Python 3.12.
- [ ] Define ordinary configuration for capture selection, entertainment area, detection thresholds, timings, logging, and post-stream behavior.
- [ ] Keep credentials in a separate protected file with restrictive permissions.
- [ ] Preserve direct use of the existing client.json or provide an explicit, reversible migration tool.
- [ ] Add validation with useful errors and no secret values in logs.
- [ ] Document setup without requiring Docker.
- [ ] Verify that installation steps leave host CUPS untouched and do not alter airprint or other Docker packages, services, networks, containers, or permissions.

### Acceptance criteria

- [ ] A fresh environment can be created from version-controlled instructions and dependency metadata.
- [ ] Non-secret configuration has a documented example.
- [ ] Secret storage is ignored, permission-checked, and compatible with current credentials.
- [ ] Startup fails clearly on invalid configuration without contacting unintended bridges.
- [ ] Existing manual Harmonize operation remains available.
- [ ] Rollback restores the prior environment/configuration path.

### Risks/unknowns

- OpenCV may remain partly system-built rather than fully reproducible through Python packaging.
- Hue client key formats and file permissions must remain compatible with upstream behavior.
- GStreamer plugin availability may vary across Ubuntu updates.

### Status

Not started.

## Milestone 3 — Refactor Harmonize Without Changing Behavior

### Objective

Separate the monolithic script into testable components while preserving the current Ambilight algorithm and manual behavior.

### Why it matters

Clear ownership of resources is required to fix races, recover safely, and add automation without changing visual behavior accidentally.

### Planned work

- [ ] Establish components for capture, Hue bridge/API control, frame/color analysis, HueStream packet construction, DTLS transport, and controller lifecycle.
- [ ] Replace shared mutable globals with explicit state and ownership.
- [ ] Replace fixed startup sleeps with readiness/error signaling.
- [ ] Synchronize frame and color data consistently.
- [ ] Make capture reset safe relative to active reads and preserve file/URL inputs.
- [ ] Use binary-safe HueStream transport and add packet-level tests.
- [ ] Make cleanup safe after failures at every partial startup stage.
- [ ] Create characterization tests for light-position mapping, RGB encoding, brightness behavior, and packet layout.
- [ ] Run the refactored application manually against the same capture and Hue setup only under an approved test procedure.

### Acceptance criteria

- [ ] Each named component has a narrow interface and clear resource ownership.
- [ ] Existing CLI behavior and Ambilight sampling are preserved or differences are documented and approved.
- [ ] Packet construction is binary-safe and covered by deterministic tests.
- [ ] Thread startup, shutdown, and capture reset no longer depend on arbitrary sleeps.
- [ ] Manual end-to-end operation succeeds before automation begins.
- [ ] The pre-refactor commit remains a tested rollback point.

### Risks/unknowns

- Existing text-mode OpenSSL piping may conceal protocol behavior that must be characterized before replacement.
- Correcting obvious bugs could change observable brightness or color output; compatibility comes first in this milestone.
- Hardware-only behavior cannot be fully covered by unit tests.

### Status

Not started.

## Milestone 4 — Headless Lifecycle and Reliability

### Objective

Make Harmonize run indefinitely without a terminal, with deterministic startup, shutdown, cleanup, recovery, and logging.

### Why it matters

An appliance service must survive routine errors and obey operating-system lifecycle requests without leaving capture or Hue resources stuck.

### Planned work

- [ ] Remove runtime dependence on input(), screen, and interactive reset/quit commands.
- [ ] Handle SIGTERM and SIGINT through a single idempotent shutdown path.
- [ ] Bound network, capture, subprocess, and thread shutdown waits.
- [ ] Clean up correctly after failures before and after Hue streaming begins.
- [ ] Implement capture reopen with backoff and the original configured source.
- [ ] Detect and recover failed DTLS and Hue stream sessions.
- [ ] Add structured, severity-based, journald-friendly logging with secret redaction.
- [ ] Define health and liveness indicators usable by systemd and diagnostics.
- [ ] Run an extended manual soak test before adding automatic source control.

### Acceptance criteria

- [ ] The application starts and stops without a terminal.
- [ ] SIGTERM and SIGINT produce clean, bounded shutdown.
- [ ] Injected partial startup failures release every acquired resource.
- [ ] Capture and transport failures recover or exit with an actionable status.
- [ ] Logs identify state and failures without credential material.
- [ ] The soak-test duration and results are recorded with a rollback commit.

### Risks/unknowns

- Hue API operations can hang or fail independently of DTLS.
- Capture reopening may require device re-enumeration rather than a simple OpenCV reopen.
- Aggressive restart behavior could contend with hardware or the bridge.

### Status

Not started.

## Milestone 5 — Automatic Ambilight State Machine

### Objective

Keep the controller running continuously while starting and stopping Hue Entertainment according to measured source activity.

### Why it matters

Explicit states and transitions make unattended decisions observable, testable, and resistant to brief HDMI interruptions.

### Planned work

- [ ] Implement IDLE → SOURCE_DETECTED → STARTING → STREAMING → STOPPING → IDLE.
- [ ] Define permitted error/recovery transitions without bypassing cleanup.
- [ ] Feed the state machine with the signal selected in Milestone 1.
- [ ] Configure activation debounce, shutdown grace, minimum-on time, and recovery backoff.
- [ ] Keep capture/detection active as required while Hue streaming is stopped.
- [ ] Log every transition with reason and elapsed time.
- [ ] Test state sequences with a fake clock, fake detector, and fake Hue controller.
- [ ] Validate real transition behavior through repeated source cycles.

### Acceptance criteria

- [ ] Stable active video starts one Hue Entertainment session.
- [ ] Stable inactive video stops it after the configured grace period.
- [ ] Brief interruptions do not cause unnecessary stop/start cycles.
- [ ] The Harmonize controller remains alive in IDLE.
- [ ] Failures transition predictably and never skip required cleanup.
- [ ] Real and simulated transition results are documented.

### Risks/unknowns

- Source flapping thresholds may depend on the capture adapter and content.
- Capture must remain cheap enough in IDLE to coexist with other Pi workloads.
- Hue sessions started elsewhere may conflict with ownership assumptions.

### Status

Not started.

## Milestone 6 — Hue Light State Management

### Objective

Capture enough pre-stream Hue state to restore lights reliably, with configurable restore or off behavior after Ambilight.

### Why it matters

Automatic streaming should not leave household lighting in an unwanted state after signal loss, shutdown, or recoverable failure.

### Planned work

- [ ] Identify every Hue resource affected by the selected entertainment configuration.
- [ ] Determine which state fields can be read and restored reliably through the Hue v2 API.
- [ ] Capture state immediately before taking control and associate it with the session.
- [ ] Implement configurable post-Ambilight modes restore and off.
- [ ] Prefer restore as the default only after reliability is demonstrated.
- [ ] Define behavior when lights change externally during streaming.
- [ ] Handle process crash, bridge loss, partial restore, and stale saved-state scenarios.
- [ ] Ensure saved state contains no credentials and has safe lifecycle/permissions.
- [ ] Test against controlled light states with an explicit recovery procedure.

### Acceptance criteria

- [ ] Normal stop produces the configured post-Ambilight result for every affected light.
- [ ] Restore accurately handles representative on/off, brightness, and color states supported by the selected lights.
- [ ] Partial failures are logged and retried or surfaced without infinite loops.
- [ ] Stale state cannot unexpectedly overwrite newer household changes.
- [ ] A documented manual recovery procedure exists.
- [ ] The pre-state-management behavior remains a rollback option.

### Risks/unknowns

- Entertainment mode and normal Hue state can expose different resource models.
- Gradient products may require grouped and per-segment considerations.
- Perfect restoration may be impossible for dynamic scenes or concurrent external control.
- Crash recovery needs careful rules to avoid applying stale state.

### Status

Not started.

## Milestone 7 — systemd Appliance Deployment

### Objective

Install Harmonize as a native, boot-started Ubuntu service with least-privilege hardware access and safe restart behavior.

### Why it matters

systemd provides lifecycle, logging, dependency ordering, and recovery needed for unattended operation without adding Docker as a dependency.

### Planned work

- [ ] Record Docker units, airprint health, active containers, resource use, working-print validation, and the intentionally inactive host-CUPS state before installation.
- [ ] Choose an unprivileged service identity and grant only required video-device and configuration access.
- [ ] Create a hardened service unit with explicit working directory, environment, restart policy, timeouts, and signal handling.
- [ ] Use stable capture-device identification rather than assuming /dev/video0 where practical.
- [ ] Route logs to journald and document inspection commands.
- [ ] Define ordering against local network readiness without blocking airprint or other Docker workloads and without modifying host CUPS.
- [ ] Install through a reversible procedure that backs up any replaced files.
- [ ] Enable boot start and test clean stop, restart, failure restart, and shutdown.
- [ ] Measure CPU, memory, and device impact in IDLE and STREAMING.
- [ ] Do not Dockerize Harmonize unless later evidence establishes a compelling benefit.

### Acceptance criteria

- [ ] Harmonize starts automatically after reboot as an unprivileged user.
- [ ] It can access only the required capture and configuration resources.
- [ ] Restart policy handles failures without a tight loop.
- [ ] journald contains useful, secret-free lifecycle logs.
- [ ] Shutdown releases Hue and capture resources within configured timeouts.
- [ ] The airprint container remains healthy and printing matches its recorded functional baseline.
- [ ] Docker and every other recorded existing workload match their baselines; host CUPS remains untouched.
- [ ] Uninstall/rollback restores the exact pre-install service state.

### Risks/unknowns

- User pi currently lacks Docker socket access, so airprint and other workload validation need an authorized read-only method.
- Host CUPS must remain inactive, disabled, and unmodified because airprint owns the production print path.
- Device enumeration and network readiness can differ at boot.
- Service hardening options may restrict OpenSSL, DNS/mDNS, or device access unexpectedly.

### Status

Not started.

## Milestone 8 — Ambilight Quality Improvements

### Objective

Evaluate visual improvements only after reliable unattended operation is proven.

### Why it matters

Quality work should be measurable and reversible, and must not destabilize lifecycle behavior or hide regressions from the refactor.

### Planned work

- [ ] Capture repeatable reference clips and baseline latency, CPU use, update rate, and representative color output.
- [ ] Evaluate temporal color smoothing.
- [ ] Correct and make brightness limiting behavior explicit.
- [ ] Evaluate saturation and gamma correction.
- [ ] Evaluate black-bar detection and improved edge sampling regions.
- [ ] Define dark-scene behavior.
- [ ] Evaluate scene-change response.
- [ ] Make update rate configurable within Hue bridge limits.
- [ ] Introduce each improvement separately with objective comparisons and an off switch.

### Acceptance criteria

- [ ] Appliance lifecycle tests continue to pass with every enabled enhancement.
- [ ] Each accepted option has documented defaults, bounds, performance cost, and rollback.
- [ ] Measured latency and CPU use remain within agreed Pi 5 limits.
- [ ] Visual changes are compared against the preserved baseline.
- [ ] Enhancements can be disabled independently.

### Risks/unknowns

- Smoothing can improve stability while increasing perceived latency.
- Black-bar and dark-scene logic can misclassify intentional content.
- Higher analysis cost can interfere with Docker, printing, or capture timing.
- Subjective improvements require consistent test content and viewing conditions.

### Status

Not started.

## Milestone 9 — Final Validation and Documentation

### Objective

Prove the complete appliance behavior across normal operation, failures, reboot, and coexistence, then document operation and recovery.

### Why it matters

The project is complete only when it can be maintained and recovered without reconstructing decisions from source code or terminal history.

### Planned work

- [ ] Test a full Pi reboot and automatic service startup.
- [ ] Test TV/source on and verify automatic streaming.
- [ ] Test source standby/off and the configured light-state result.
- [ ] Test TV off while the source remains active.
- [ ] Test repeated on/off cycles and brief signal interruptions.
- [ ] Test temporary capture failure and reconnection.
- [ ] Test temporary Hue/network failure where practical and safe.
- [ ] Test service stop, start, restart, failure restart, SIGTERM, and shutdown.
- [ ] Verify that the airprint container remains healthy and complete a working-print check.
- [ ] Verify Docker service and every other recorded workload against baseline; confirm host CUPS was not modified.
- [ ] Record idle/streaming CPU, memory, temperature, frame rate, and recovery timing.
- [ ] Document installation, configuration, credentials, operation, logs, troubleshooting, updates from upstream, backup, and rollback.
- [ ] Perform a clean-install rehearsal or equivalent reproducibility review.
- [ ] Record the final accepted commit and release/tag.

### Acceptance criteria

- [ ] Every end-to-end scenario has a recorded result and any failure has an explicit disposition.
- [ ] Repeated source cycles do not leak processes, threads, file descriptors, Hue sessions, or unwanted light state.
- [ ] Reboot and service recovery require no terminal interaction.
- [ ] Airprint printing and all other Docker workloads remain functional according to recorded baselines; host CUPS remains untouched.
- [ ] A new operator can install, configure, diagnose, update, and roll back using the documentation.
- [ ] Credentials are absent from Git history, logs, examples, and diagnostic bundles produced by the modernization work.
- [ ] The final release has a clear previous known-good rollback point.

### Risks/unknowns

- Some network and bridge failures may be difficult to reproduce safely.
- Reboot ordering can expose races not visible in interactive testing.
- Airprint validation may require a physical print test, and Docker health inspection requires an authorized read-only access method.
- Long-duration reliability may reveal thermal or resource contention not seen in short tests.

### Status

Not started.
