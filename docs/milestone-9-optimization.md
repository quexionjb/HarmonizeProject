# Milestone 9: Ambilight quality optimization plan

## Purpose and scope

This document is the persistent test plan and experiment log for Milestone 9.
It supplements the Milestone 9 roadmap in `PROJECT.md`. Update it as work
progresses so future sessions can identify the control behavior, measurements,
approved experiments, rejected ideas, rollback choices, and current accepted
configuration.

The goal is to improve responsiveness and reduce latency where worthwhile while
preserving the visual character and appliance reliability of the released
v3.0.0 implementation. This milestone favors measured, incremental,
independently reversible changes over broad algorithm changes.

The subjective starting point is intentionally conservative:

- The current Ambilight effect already looks good.
- Responsiveness and latency are higher priorities than visual redesign.
- Historical brightness behavior remains part of the control, even where its
  semantics are mathematically unusual.
- Letterboxed content is common, but black-bar handling is justified only if
  measurements show that bars affect the configured sampling regions.
- An optimization that is not measurably or noticeably better while looking at
  least as good as v3.0.0 should be rejected.

## Released control and discovery baseline

The control is released v3.0.0 at commit
`6aec8cca7afbaf05c3923f79afac5108799cb1a4`. The Milestone 9 topic branch is
`m9-ambilight-quality`.

### Sampling

Each Hue Entertainment channel has an independently calculated rectangular
sampling region. Hue `x` maps horizontally, Hue `z` maps vertically with its
sign inverted, and Hue `y` is ignored. The sample distance is:

```text
int(sample_breadth * (frame_width / 2 + frame_height / 2))
```

That distance extends in all four directions from the mapped channel position,
with the result clipped to the frame edges. The deployed `sample_breadth` is
`0.15`.

At the previously measured 720x480 capture format, the distance is 90 pixels.
A typical channel placed at the left or right midpoint therefore samples a
side region approximately 90x180 pixels after edge clipping. The algorithm
does not divide the frame into one half per light; each channel is evaluated
independently from its Hue coordinates.

For the current two-light left/right arrangement, ordinary top and bottom
letterboxing probably does not intersect midpoint sampling regions. Bars could
strongly affect vertically positioned channels, however, so actual channel
geometry and frame/bar boundaries must be measured before implementing
black-bar handling.

### Brightness and output

Current multi-light processing is:

1. Convert the complete BGR frame to HSV.
2. Add the configured brightness adjustment to HSV value, clipping the upper
   end at 255.
3. Convert the adjusted frame back to BGR and then to RGB.
4. Arithmetic-mean red, green, and blue independently within each channel's
   sampling region.
5. Divide each 8-bit mean by two using integer truncation.
6. Repeat that byte as the high and low bytes of the HueStream 16-bit RGB
   component.
7. Send one RGB triplet per channel through the Entertainment DTLS stream.

There is no separate streamed Hue brightness field. Perceived brightness
results from RGB magnitude. Dark pixels and black bars therefore reduce the
regional channel means directly. Averaging different colors can also reduce
saturation.

The historical divide-by-two encoding limits the greatest streamed component
to 32,639 of 65,535, approximately half the available numeric range. The
deployed `brightness_adjustment` is `0`. Positive adjustment values brighten
HSV value rather than acting as a maximum-brightness percentage. Negative
values are accepted by configuration but fail against the unsigned NumPy value
array instead of reliably darkening the image.

These confusing semantics are part of the current good-looking baseline.
Brightness cleanup or full-range output is a later controlled visual
experiment, not an initial correction.

### Timing and latency

The deployed `update_interval_seconds` is `0.05`, applied after each completed
packet send. Its nominal ceiling is therefore 20 updates per second. A passive
live observation during discovery measured system UDP output consistent with
approximately 19 Hue updates per second.

The capture worker continuously drains its OpenCV source, retains only the
newest application-level frame, and wakes the controller when a newer
generation is available. Earlier controlled capture work measured about 55
frames per second at 720x480 using the Harmonize-style GStreamer path. The
deployed service now uses the direct V4L2 backend and does not log its
negotiated resolution or frame rate, so those live values remain to be
measured.

During the discovery observation, OpenCV/V4L2 rejected
`CAP_PROP_BUFFERSIZE=0`. The application discards superseded frames, but
capture-device, kernel, or backend buffering below that boundary remains an
unknown. End-to-end video-to-photon latency has not yet been measured. The
explicit 50 ms pacing alone can delay the next update by up to approximately
50 ms, or approximately 25 ms on average for randomly timed visual changes.

Other latency sources include HDMI/capture conversion, frame acquisition and
decode, whole-frame color conversion, regional analysis, synchronous DTLS
pipe writes, LAN/bridge processing, and light rendering. A synchronous Hue
status query in the controller can also introduce an occasional packet gap at
its configured interval.

### Runtime cost

The discovery sample found substantial Raspberry Pi 5 headroom while
STREAMING:

- Harmonize Python averaged about 59% of one CPU core and roughly 95 MiB RSS.
- The OpenSSL DTLS child used negligible CPU and roughly 8 MiB RSS.
- The service cgroup used roughly 118 MiB current and 143 MiB peak memory.
- The four-core host load average was below 1, with roughly 3 GiB RAM
  available and a temperature near 49 degrees Celsius.
- No service restart or recovery event occurred.

Capture and decode appear to dominate CPU use. Packet construction and OpenSSL
transmission are not promising optimization targets by themselves.

## Optimization experiment sequence

Only one meaningful variable should change in each experiment. Do not make a
trial setting the new default until its measurements and visual comparison have
been reviewed.

### Step 1 - Instrumentation and 50 ms control

Add lightweight instrumentation sufficient to measure:

- negotiated capture resolution and reported FPS;
- capture-frame arrival timing;
- frame age when analysis begins;
- analysis duration;
- packet/update interval and effective packet rate;
- skipped or replaced application-level frames where practical;
- unusually long packet gaps;
- CPU and RSS; and
- service stability and recovery events.

Establish a measured control with
`update_interval_seconds = 0.05`. Do not change visual processing in this
step. Instrumentation must avoid per-frame INFO logging or other measurement
overhead large enough to perturb the pipeline.

### Step 2 - 33 ms pacing

Change only `update_interval_seconds` to `0.033`, targeting approximately 30
updates per second. Compare directly with the 50 ms control:

- actual update rate and packet consistency;
- frame age and analysis duration;
- CPU and RSS;
- Hue/DTLS errors and unusually long gaps;
- service stability; and
- subjective responsiveness and visual quality.

Do not automatically make 33 ms the permanent default. Restore `0.05` after
the trial unless the result is explicitly accepted.

### Step 3 - 20 ms pacing, only if justified

Test `update_interval_seconds = 0.020` only if the 33 ms trial is completely
stable and its results suggest that a higher send rate could provide a further
benefit. Compare 20 ms directly with 33 ms, not only with the original 50 ms
control. Reject it if increased traffic or CPU produces no meaningful
responsiveness improvement.

### Step 4 - Capture and frame-age investigation

Use the instrumentation to determine whether frames reaching Harmonize are
already stale because of capture-device, V4L2, or backend buffering. The
application already retains its newest available frame, so do not redesign
that mechanism without evidence.

If measurements demonstrate meaningful lower-level buffering, test one
controlled low-buffer alternative, such as a supported V4L2 setting or a
drop-enabled GStreamer pipeline. Preserve the current direct V4L2 path for
immediate rollback.

### Step 5 - Brightness-zero analysis fast path

Because the deployed brightness adjustment is zero, investigate bypassing the
whole-frame BGR-to-HSV-to-BGR round trip only when the adjustment is exactly
zero. Accept this optimization only if deterministic characterization tests
show that final HueStream RGB bytes remain byte-for-byte identical to the
released algorithm. Its purpose is CPU reduction, not a visual change, and the
legacy path must remain available during evaluation.

### Step 6 - Black-bar measurement

Measure actual channel geometry and sampling-region overlap with representative
letterboxed frames. Do not implement black-bar detection merely because bars
are present somewhere in the frame.

Test black-bar-aware sampling only if measurements show meaningful overlap.
Any implementation must be optional, robust against intentionally dark scenes,
and able to restore the legacy fixed-region behavior independently.

## Deferred visual experiments

Do not prioritize the following until timing and capture optimization have
been completed and evaluated:

- temporal smoothing;
- gamma correction;
- saturation adjustment;
- full-range brightness/output redesign;
- major sampling-region changes;
- scene-change processing; and
- dominant-color or max-pixel selection.

Temporal smoothing is particularly low priority because it adds latency, which
conflicts with the current goal. Aggressive dominant-color selection risks
overreacting to subtitles, isolated highlights, and noise. Brightness,
saturation, gamma, and major region changes all have a higher risk of making
the current good-looking output worse and therefore require separate opt-in
controls and visual comparisons.

## Comparison content

Where practical, compare each candidate with the same representative scenes
and viewing conditions:

- fast scene cuts and action;
- slow pans;
- dark scenes;
- bright scenes;
- strong left/right color contrast; and
- letterboxed content.

Reference material must not be committed unless its licensing and repository
size are appropriate. Record enough identifying information to repeat a test
without storing protected content.

## Safety and acceptance rules

For every experiment:

- preserve released v3.0.0 behavior as the control;
- change one meaningful variable at a time;
- measure before and after;
- keep the change small and reversible;
- provide an off switch or direct rollback where practical;
- preserve systemd lifecycle, local Unix-socket control, HTTP control, and
  HomeKit integration;
- never expose Hue credentials;
- leave Docker, AirPrint, host CUPS, and unrelated services untouched; and
- avoid visual complexity merely because it is technically possible.

The acceptance question is: does this make Harmonize measurably or noticeably
more responsive while still looking as good as the released version? If not,
retain the simpler released behavior.

## Experiment log

Add one entry for each control measurement or experiment. Do not rewrite prior
results; append corrections or follow-up entries so the decision history
remains clear.

### Entry template

```text
Date:
Experiment/step:
Commit:
Configuration:
Test content/conditions:
Measurements:
Subjective observation:
Result: accepted | rejected | inconclusive
Rollback/default decision:
Notes/follow-up:
```

### Recorded entries

No optimization experiment has started. The observations above are the
discovery baseline and must be converted into an instrumented 50 ms control in
Step 1 before pacing or algorithm trials begin.
