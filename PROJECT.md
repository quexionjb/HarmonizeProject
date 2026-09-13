# Harmonize Modernization Project

## Objective

Turn Harmonize into an appliance-like Ambilight service on this Raspberry Pi 5 running Ubuntu. The service should run unattended, detect whether the HDMI/video source is worth illuminating, start and stop Hue Entertainment streaming automatically, and restore the affected lights or turn them off afterward. It must coexist safely with the production airprint Docker print service and the Pi's other Docker workloads; host-level CUPS is intentionally inactive and out of scope.

This roadmap is the persistent tracker for that work. Implementation stops at every milestone boundary for review and explicit authorization.

## Current Baseline

- Hardware: Raspberry Pi 5, 64-bit ARM.
- Operating system: Ubuntu with Linux 6.8.0-1064-raspi observed during initial discovery.
- Python: 3.12.3 in both the system interpreter and /home/pi/harmonize_env.
- Computer vision: OpenCV 4.10.0 with GStreamer 1.24.2, FFmpeg, and V4L2 support; NumPy 1.26.4.
- Capture: /dev/video0 and /dev/video1 exist, along with Pi codec devices. User pi belongs to the video group. Milestone 1 found capture activity independent of TV power in the current splitter topology.
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

## Target Controller Architecture

The future daemon separates desired state from lifecycle execution:

    Desired-state providers
      - local command/API
      - Homebridge/HomeKit adapter (future)
      - HDMI-CEC provider (future, unavailable in current wiring)
      - other automation providers
                |
                v
      normalized desired state
      enabled/disabled + source + timestamp
                |
                v
      Harmonize lifecycle controller
      IDLE -> STARTING -> STREAMING -> STOPPING -> IDLE
                |
                v
      capture, Hue session, DTLS, and light-state components

The lifecycle controller must not contain provider-specific logic. It accepts a desired state and exposes actual state, transition progress, and errors. The initial production control surface should support Ambilight ON, Ambilight OFF, and Ambilight STATUS through a small local API or command interface. Homebridge may later map that interface to an Ambilight switch without becoming a required Harmonize dependency.

Automatic providers must be optional and replaceable. Manual control must remain available when no reliable automatic TV-state signal exists. Provider arbitration, authentication, stale-command handling, and fail-safe behavior will be specified before implementation.

## Hue Integration Testing Policy

Hue validation proceeds in controlled stages:

- Milestone 2 uses offline configuration, schema, and credential-path tests. It defines the non-secret setting hue.entertainment_area = "TV area" but does not require a live bridge.
- Milestone 3 begins with a read-only live query that resolves the configured area name to exactly one bridge resource. A missing or ambiguous area must fail with an actionable error before Entertainment streaming starts.
- Milestone 3 then performs a separately approved manual start/stream/stop test against only the configured TV area after offline component tests pass.
- Milestone 4 exercises live partial-startup cleanup, DTLS/bridge recovery, signals, and bounded shutdown under an approved failure-injection procedure.
- Milestone 5 validates explicit ON/OFF/STATUS lifecycle cycles against the configured area after provider and state-machine tests pass offline.
- Milestone 6 performs controlled live light-state capture and restore/off tests with a recorded manual recovery procedure.
- Milestone 9 repeats end-to-end Hue validation, including missing-area, temporary network failure, service restart, cleanup, and post-Ambilight light state.

Every live-Hue test requires a stated scope, expected light behavior, cleanup path, and rollback point. Record the selected Entertainment area and pre/post state without logging credentials. Confirm streaming is stopped after each test, including failed tests. Do not contact or control the bridge merely to validate parsing or other behavior that can be tested offline.

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

Determine whether the installed capture and HDMI topology exposes a reliable TV-power signal, evaluate direct HDMI-CEC, and define a safe explicit-control fallback when automatic detection is unavailable.

### Why it matters

The Roku can keep valid HDMI video flowing to the capture branch while the television is off. Appliance control must use actual desired state rather than infer TV power from brittle content assumptions.

### Planned work

- [x] Record USB identity, driver, V4L2 capabilities, supported formats, resolutions, and frame rates for /dev/video0.
- [x] Measure frame availability, read latency, timestamps, resolution, and device state with active Roku video.
- [x] Measure the capture device with the HDMI source off or in standby.
- [x] Document the independent Roku → splitter → TV/capture topology and TV-off behavior.
- [x] Stop content comparison once capture activity was proven independent of TV power.
- [x] Exclude Roku Home, screensaver, black-frame, image-hash, and other content-specific heuristics.
- [x] Inventory Pi HDMI connectors, CEC nodes, kernel support, physical addresses, and USB capture interfaces.
- [x] Determine whether the existing wiring exposes the television's CEC bus to the Pi.
- [x] Build a repeatable, non-recording capture diagnostic and record results.
- [x] Define explicit ON/OFF/STATUS control and a modular desired-state provider boundary as the production fallback.
- [x] Avoid Hue bridge contact and control throughout the milestone.

### Acceptance criteria

- [x] Active-source and source-standby capture behavior are repeatably characterized.
- [x] The TV-off/Roku-active topology limitation is documented without content-specific workarounds.
- [x] Capture activity is classified as unreliable for TV-power detection in this topology.
- [x] Direct HDMI-CEC is classified as unavailable with the current physical wiring.
- [x] The recommended explicit-control design is independent of capture and future trigger source.
- [x] No Hue state, host CUPS service, airprint container, or other Docker workload was changed.
- [x] Findings and the rollback commit are recorded before Milestone 2.

### Risks/unknowns

- A future Pi HDMI or dedicated CEC connection to the television would create a different topology requiring new validation.
- Homebridge may or may not already expose a reliable Roku/TV state suitable for later automation.
- The local control transport and provider arbitration rules remain Milestone 2 design decisions.
- /dev/video numbering stability still matters for capture operation even though capture no longer supplies TV power state.

### Status

Complete. Direct CEC and capture-based TV-power detection are unavailable in the current topology. Explicit modular desired-state control is recommended. Stop for review before Milestone 2.

## Milestone 2 — Establish Configuration and Dependency Boundaries

### Objective

Create a reproducible Python environment and a validated configuration layer while safely preserving existing Hue credentials.

### Why it matters

The current manually assembled environment and script-level options are difficult to reproduce, audit, deploy, and recover.

### Planned work

- [x] Inventory imports and system dependencies, including OpenCV/GStreamer and the OpenSSL DTLS requirement.
- [x] Choose and document a reproducible Python dependency specification compatible with aarch64 Ubuntu and Python 3.12.
- [x] Define ordinary non-secret configuration for capture selection, detection/provider settings, timings, logging, post-stream behavior, and hue.entertainment_area = "TV area"; the area value comes from configuration and is not a hard-coded application constant.
- [x] Require unattended mode to resolve one configured default Entertainment area deterministically, without input() or any other prompt.
- [x] Preserve legacy/manual interactive area selection when practical, while treating it as an explicit compatibility mode rather than a service fallback.
- [x] Keep credentials in a separate protected file with restrictive permissions.
- [x] Preserve direct use of the existing client.json with a reversible permission-hardening path.
- [x] Add validation with useful errors and no secret values in logs.
- [x] Document setup without requiring Docker.
- [x] Verify that installation steps leave host CUPS untouched and do not alter airprint or other Docker packages, services, networks, containers, or permissions.

### Acceptance criteria

- [x] The documented non-secret example includes hue.entertainment_area = "TV area" with exact capitalization.
- [x] Unattended configuration validation requires a non-empty default area and never prompts.
- [x] Offline tests cover missing configuration and legacy/manual fallback without contacting the bridge.
- [x] Live area existence and uniqueness validation is explicitly deferred to the approved Milestone 3 bridge test.
- [x] A fresh environment can be created from version-controlled instructions and dependency metadata.
- [x] Non-secret configuration has a documented example.
- [x] Secret storage is ignored, permission-checked, and compatible with current credentials.
- [x] Startup fails clearly on invalid configuration without contacting unintended bridges.
- [x] Existing manual Harmonize operation remains available unchanged.
- [x] Rollback restores the prior environment/configuration path.

### Risks/unknowns

- OpenCV 4.10.0 is a documented system boundary because the accepted local build supplies required GStreamer support; a generic wheel is not an equivalent replacement.
- Entertainment-area names can be renamed or duplicated on the bridge; live resolution must reject zero or multiple exact matches.
- A future stable Hue resource ID may be stored as an optional resolved value, but the configured human-readable default remains ordinary configuration.
- The existing compatible client.json is mode 0664. Manual validation warns and continues; unattended validation requires the owner to apply the documented chmod 600 correction. Milestone 2 did not alter the file.
- GStreamer plugin availability may vary across Ubuntu updates.

### Status

Complete on branch m2-config-boundaries. Offline typed configuration, credential
validation, reproducible Python dependency metadata, tests, and setup/rollback
instructions are present. The legacy runtime and credentials remain unchanged.
Live Hue area existence/uniqueness validation is deferred to Milestone 3 as
planned. Stop for review before Milestone 3.

## Milestone 3 — Refactor Harmonize Without Changing Behavior

### Objective

Separate the monolithic script into testable components while preserving the current Ambilight algorithm and manual behavior.

### Why it matters

Clear ownership of resources is required to fix races, recover safely, and add automation without changing visual behavior accidentally.

### Planned work
- [ ] Add Hue area resolution that maps the exact configured name TV area to one Entertainment configuration before any start request.
- [ ] Keep legacy/manual interactive selection available when practical, but prohibit it in unattended mode.

- [ ] Establish components for capture, Hue bridge/API control, frame/color analysis, HueStream packet construction, DTLS transport, and controller lifecycle.
- [ ] Replace shared mutable globals with explicit state and ownership.
- [ ] Replace fixed startup sleeps with readiness/error signaling.
- [ ] Synchronize frame and color data consistently.
- [ ] Make capture reset safe relative to active reads and preserve file/URL inputs.
- [ ] Use binary-safe HueStream transport and add packet-level tests.
- [ ] Make cleanup safe after failures at every partial startup stage.
- [ ] Run a separately approved read-only live test confirming TV area exists and test an unknown configured name for a clear pre-stream error.
- [ ] Run a separately approved manual start/stream/stop test scoped to TV area and verify cleanup afterward.
- [ ] Create characterization tests for light-position mapping, RGB encoding, brightness behavior, and packet layout.
- [ ] Run the refactored application manually against the same capture and Hue setup only under an approved test procedure.

### Acceptance criteria

- [ ] Each named component has a narrow interface and clear resource ownership.
- [ ] Existing CLI behavior and Ambilight sampling are preserved or differences are documented and approved.
- [ ] Packet construction is binary-safe and covered by deterministic tests.
- [ ] Thread startup, shutdown, and capture reset no longer depend on arbitrary sleeps.
- [ ] Unattended execution resolves TV area deterministically with no prompt.
- [ ] Missing or ambiguous configured areas fail before streaming with an actionable message naming the configured value.
- [ ] The approved live Hue test confirms streaming starts and stops only for the resolved TV area.
- [ ] Manual end-to-end operation succeeds before automation begins.
- [ ] The pre-refactor commit remains a tested rollback point.

### Risks/unknowns

- Existing text-mode OpenSSL piping may conceal protocol behavior that must be characterized before replacement.
- Renaming or duplicating TV area after configuration must produce a safe startup failure rather than an interactive prompt or arbitrary selection.
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

- [ ] Remove runtime dependence on input(), screen, interactive reset/quit commands, and interactive Entertainment-area selection.
- [ ] Handle SIGTERM and SIGINT through a single idempotent shutdown path.
- [ ] Bound network, capture, subprocess, and thread shutdown waits.
- [ ] Revalidate the configured Entertainment area during startup and recover safely if it was renamed, removed, or became ambiguous.
- [ ] Exercise approved live partial-startup and shutdown failures and verify Entertainment streaming is stopped afterward.
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
- [ ] Headless startup never waits for Entertainment-area input.
- [ ] Live failure-injection results demonstrate cleanup of the configured TV area without leaving an active session.
- [ ] The soak-test duration and results are recorded with a rollback commit.

### Risks/unknowns

- Hue API operations can hang or fail independently of DTLS.
- Capture reopening may require device re-enumeration rather than a simple OpenCV reopen.
- Aggressive restart behavior could contend with hardware or the bridge.

### Status

Not started.

## Milestone 5 — Automatic Ambilight State Machine

### Objective

Keep the controller running continuously while starting and stopping Hue Entertainment according to a normalized desired state supplied by a modular trigger provider.

### Why it matters

The lifecycle must behave consistently whether desired state comes from manual local control, future Homebridge automation, future CEC hardware, or another provider.

### Planned work

- [ ] Implement IDLE → STARTING → STREAMING → STOPPING → IDLE with explicit error/recovery transitions.
- [ ] Define a provider interface that emits enabled/disabled desired state with source and timestamp.
- [ ] Implement a small local command or API surface for Ambilight ON, OFF, and STATUS.
- [ ] Keep provider-specific logic outside capture, Hue, DTLS, cleanup, and light-state components.
- [ ] Define precedence, authentication, stale-command expiry, and fail-safe behavior for multiple providers.
- [ ] Make automatic providers optional; do not require HDMI-CEC or Homebridge.
- [ ] Apply debounce and grace periods to automatic providers while keeping explicit commands deterministic.
- [ ] Expose desired state, actual lifecycle state, transition progress, provider source, and errors.
- [ ] Log every transition with reason and elapsed time.
- [ ] Test state sequences with a fake clock, fake provider, and fake Hue controller.
- [ ] Run approved live ON/OFF/STATUS cycles against the configured TV area and confirm each final state.
- [ ] Validate repeated explicit ON/OFF cycles before enabling any automatic provider.
- [ ] Defer Homebridge/HomeKit integration until separately authorized.

### Acceptance criteria

- [ ] An ON command starts one Hue Entertainment session and reaches STREAMING.
- [ ] An OFF command reaches IDLE after complete cleanup and configured light-state handling.
- [ ] STATUS distinguishes desired state, actual state, transition state, and errors.
- [ ] The same lifecycle tests pass with interchangeable fake providers.
- [ ] Provider loss or stale state follows a documented fail-safe policy.
- [ ] The Harmonize controller remains alive in IDLE.
- [ ] Failures transition predictably and never skip required cleanup.
- [ ] Live lifecycle tests affect only the configured TV area and leave its Entertainment session stopped.
- [ ] Homebridge is not a runtime dependency of the core daemon.

### Risks/unknowns

- A network API needs access control and should default to a Unix socket or loopback-only binding.
- Multiple providers can conflict or leave stale desired state.
- Automatic state sources may flap and need provider-specific policy.
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
- [ ] Run approved live restore and off tests only against lights in the resolved TV area.
- [ ] Record pre-test state and verify post-test state after normal stop and injected failure.
- [ ] Test against controlled light states with an explicit recovery procedure.

### Acceptance criteria

- [ ] Normal stop produces the configured post-Ambilight result for every affected light.
- [ ] Restore accurately handles representative on/off, brightness, and color states supported by the selected lights.
- [ ] Partial failures are logged and retried or surfaced without infinite loops.
- [ ] Stale state cannot unexpectedly overwrite newer household changes.
- [ ] Live Hue integration tests prove both restore and off behavior and leave no active Entertainment session.
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
- [ ] Configure the service with the default TV area and verify boot startup cannot enter an interactive selection path.
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
- [ ] Boot and restart tests deterministically resolve the configured TV area or fail clearly without prompting.
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
- [ ] Test exact resolution of TV area and the actionable failure for a missing or ambiguous configured area.
- [ ] Verify every live test and service stop leaves Hue Entertainment streaming disabled.
- [ ] Verify only the configured Entertainment area and its affected lights change during controlled tests.
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
- [ ] The full Hue validation matrix passes for area resolution, streaming lifecycle, recovery, and post-Ambilight state.
- [ ] Installation documentation explains the default area setting, exact-name matching, legacy/manual selection, and failure recovery.
- [ ] The final release has a clear previous known-good rollback point.

### Risks/unknowns

- Some network and bridge failures may be difficult to reproduce safely.
- Reboot ordering can expose races not visible in interactive testing.
- Airprint validation may require a physical print test, and Docker health inspection requires an authorized read-only access method.
- Long-duration reliability may reveal thermal or resource contention not seen in short tests.

### Status

Not started.
