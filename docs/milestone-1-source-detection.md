# Milestone 1: Source Activity Detection

## Safety boundary

This milestone observes the USB capture path and local HDMI-CEC availability. It does not contact or control the Hue bridge. It must not modify host-level CUPS, the production airprint container, or any other Docker workload.

## Capture hardware inventory

- Capture device: MacroSilicon WARRKY USB 3.0
- USB identity: vendor 345f, model 2130, serial 62196249
- Driver: uvcvideo
- Primary capture node: /dev/video0
- Companion node: /dev/video1
- Stable primary path: /dev/v4l/by-id/usb-MACROSILICON_WARRKY_USB_3.0_62196249-video-index0
- Harmonize-compatible access: OpenCV device index 0 with the GStreamer backend
- The stable by-id path does not open through OpenCV's automatic GStreamer pipeline on this installation. Stable selection will need either index resolution before opening or an explicit pipeline.
- User pi belongs to the video group.
- No process held /dev/video0 or /dev/video1 during the initial inventory.

GStreamer reports MJPEG formats through 1920x1080 and YUY2 formats through 1920x1080. Relevant examples include:

- MJPEG 1920x1080 at 10, 20, 25, 30, or 50 FPS
- MJPEG 1280x720 at 10, 20, 30, 50, or 60 FPS
- YUY2 1920x1080 at 5 or 10 FPS
- YUY2 1280x720 at 10 or 20 FPS
- YUY2 720x480 at 10, 20, 30, or 60 FPS

An unconstrained v4l2src probe negotiated MJPEG 1280x1024 at 60 FPS. The current Harmonize-style OpenCV/GStreamer path negotiates decoded 720x480 frames and reports 60 FPS.

## Repeatable probe

Run the probe from the project virtual environment under an outer timeout:

    timeout 25s /home/pi/harmonize_env/bin/python tools/capture_probe.py \
      --label CONDITION --duration 15

The probe saves no frames. It reports device-open success, reported format, successful and failed reads, first-frame latency, effective frame rate, read timing, interarrival timing, and observed shapes. Pixel-derived aggregate metrics are disabled by default. If frame delivery cannot distinguish active and inactive states, add --content-metrics; this still saves no frames.

An outer timeout is required because a driver-level OpenCV read can block beyond the requested duration when frames stop arriving.

## Initial unclassified observation

At 2026-09-13T18:59:14Z, the current physical HDMI/TV state had not yet been confirmed:

- Open succeeded through GStreamer.
- Reported format was 720x480 at 60 FPS.
- 276 frames succeeded and zero reads failed in 5.010 seconds.
- Effective rate was 55.091 FPS.
- First frame arrived in 1.562 ms.
- Median interarrival time was 18.122 ms; 95th percentile was 18.222 ms; maximum was 31.602 ms.
- No resolution or shape change occurred.
- Content metrics were not collected.

This sample proves continuous frame delivery in the current state. It does not yet prove that frame delivery distinguishes useful HDMI video from standby behavior.

## Controlled active-source observation

At 2026-09-13T19:02:03Z, the TV was on and the HDMI source was confirmed actively playing:

- Open succeeded through GStreamer.
- Reported format was 720x480 at 60 FPS.
- 828 frames succeeded and zero reads failed in 15.011 seconds.
- Effective rate was 55.161 FPS.
- First frame arrived in 1.478 ms.
- Median interarrival time was 18.124 ms; 95th percentile was 18.217 ms; maximum was 31.041 ms.
- No resolution or shape change occurred.
- Content metrics were not collected in the first run.

A matching 15-second content-metrics run at 2026-09-13T19:09:39Z used confirmed moving video:

- 828 frames produced 827 temporal comparisons.
- Median temporal mean absolute difference was 0.718 and the 95th percentile was 3.998.
- 308 comparisons were near-identical, a fraction of 0.372430.
- Mean sampled luma had a median of 41.501 and a 95th percentile of 54.584.
- Minimum luma was 0.0 and maximum temporal difference was 61.633, including capture startup.

Moving video therefore differs strongly from the standby fallback, but paused or intentionally static active content remains a possible false-negative case.

## Controlled source-standby observation

At 2026-09-13T19:06:13Z, the TV remained on while the HDMI source was confirmed off or in standby:

- The non-content probe opened successfully and delivered 829 frames with zero failed reads in 15.026 seconds.
- Reported format remained 720x480 at 60 FPS with no shape change.
- Effective rate was 55.169 FPS and median interarrival was 18.117 ms.
- Frame delivery, timing, and format were effectively indistinguishable from active playback.

Because lower-level signals were insufficient, a second 15-second run collected aggregate content metrics without saving frames:

- 829 frames produced 828 temporal comparisons.
- Median and 95th-percentile temporal mean absolute difference were both 0.0.
- 825 comparisons were near-identical, a fraction of 0.996377.
- Mean sampled luma had a median and maximum of exactly 62.027.
- Minimum luma was 0.0 and maximum temporal difference was 62.027, consistent with a brief startup transition into a fixed fallback frame.

The WARRKY adapter therefore continues normal frame delivery in standby but appears to emit a static fallback image. Device-open state, read success, frame timing, and resolution cannot distinguish active playback from standby on their own.

## Test matrix

| Condition | Frame delivery | Timing and format | Content metrics | Result |
| --- | --- | --- | --- | --- |
| HDMI source actively playing | 828/828 frames; no failures | 720x480; 55.161 FPS; 18.124 ms median interval | 37.2430% near-identical; median temporal difference 0.718 | Continuous changing video |
| HDMI source off or in standby | 829/829 frames; no failures | 720x480; 55.169 FPS; 18.117 ms median interval | 99.6377% near-identical; median temporal difference 0.0 | Continuous static fallback |
| TV off, HDMI source active | Pending | Pending | Only if needed | Pending |
| Active to inactive transition | Pending | Pending | Only if needed | Pending |
| Inactive to active transition | Pending | Pending | Only if needed | Pending |

Use the same source, splitter, capture connection, probe duration, backend, and negotiated settings for comparisons. Record exact physical actions and allow the system to settle before steady-state samples.

## HDMI-CEC inventory

- /dev/cec0 maps to the Pi controller at 107c701400.hdmi.
- /dev/cec1 maps to the Pi controller at 107c706400.hdmi.
- The vc4 and cec kernel modules are loaded.
- cec-ctl and cec-client are not installed.
- These adapters belong to the Pi's HDMI outputs, while the video source enters through the USB capture device. Their presence alone does not show that source or TV power state is visible through the splitter topology.
- CEC remains an optional secondary signal. Frame/device behavior will be evaluated first.

## Current hypotheses

1. Frame delivery cannot distinguish active playback from source standby because both states deliver continuously.
2. Steady-state format and timing cannot distinguish those states on this adapter.
3. Aggregate temporal change is a promising signal because the standby output settles into a fixed fallback frame.
4. CEC should be excluded if the Pi output adapters cannot observe the upstream TV/source topology reliably.

## Open questions

- Which physical condition produced the initial unclassified sample?
- Does the WARRKY device continue to deliver frames with no HDMI input?
- Does the splitter preserve an HDMI signal when only the TV powers off?
- Does the capture format change during transitions?
- Is a specific /dev/video node or stable by-id mapping sufficient after reboot?
- Can CEC observe anything useful in this wiring without changing the HDMI topology?
