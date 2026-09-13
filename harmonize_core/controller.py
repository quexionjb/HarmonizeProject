"""Resource-owning Harmonize lifecycle for one manual streaming session."""

from __future__ import annotations

from enum import Enum
import threading
import time
from typing import Callable

from .analysis import FrameAnalyzer
from .capture import CaptureSource
from .errors import HarmonizeError
from .hue import EntertainmentArea, HueBridge
from .protocol import HueStreamPacketBuilder
from .transport import OpenSslDtlsTransport


class LifecycleState(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    STREAMING = "STREAMING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class HarmonizeController:
    """Own capture, Hue session, analyzer, and transport cleanup."""

    def __init__(
        self,
        *,
        hue: HueBridge,
        area: EntertainmentArea,
        capture: CaptureSource,
        client_key: str,
        brightness_adjustment: int,
        sample_breadth: float,
        update_interval_seconds: float,
        single_light: bool,
        auto_restart_seconds: float,
        transport_factory: Callable[..., OpenSslDtlsTransport] = OpenSslDtlsTransport,
    ):
        self.hue = hue
        self.area = area
        self.capture = capture
        self.client_key = client_key
        self.brightness_adjustment = brightness_adjustment
        self.sample_breadth = sample_breadth
        self.update_interval_seconds = update_interval_seconds
        self.single_light = single_light
        self.auto_restart_seconds = auto_restart_seconds
        self.transport_factory = transport_factory

        self.state = LifecycleState.IDLE
        self.error: Exception | None = None
        self.ready = threading.Event()
        self.finished = threading.Event()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None

    def start_background(self) -> None:
        if self._thread is not None:
            raise HarmonizeError("Controller has already been started")
        self._thread = threading.Thread(
            target=self.run, name="harmonize-controller", daemon=False
        )
        self._thread.start()

    def request_stop(self) -> None:
        self._stop_requested.set()

    def request_capture_reset(self) -> None:
        self.capture.request_reset()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    def run(self) -> None:
        stream_stop_required = False
        transport = None
        self.state = LifecycleState.STARTING

        def make_analyzer(frame):
            height, width = frame.shape[:2]
            return FrameAnalyzer(
                channels=self.area.channels,
                width=width,
                height=height,
                brightness_adjustment=self.brightness_adjustment,
                breadth=self.sample_breadth,
                single_light=self.single_light and len(self.area.channels) == 1,
            )

        def remember_cleanup_error(cleanup_error: Exception) -> None:
            if self.error is None:
                self.error = cleanup_error
                self.state = LifecycleState.ERROR

        try:
            if not self.area.channels:
                raise HarmonizeError(
                    f'Hue Entertainment area "{self.area.name}" has no channels'
                )
            if len(self.area.channels) > 20:
                raise HarmonizeError(
                    f'Hue Entertainment area "{self.area.name}" has '
                    f"{len(self.area.channels)} channels; maximum is 20"
                )

            self.capture.open()
            frame = self.capture.read()
            analyzer = make_analyzer(frame)
            builder = HueStreamPacketBuilder(self.area.resource_id)
            application_id = self.hue.application_id()

            # Once a start request is attempted, cleanup must issue stop even if
            # the response is lost or malformed after the bridge accepts it.
            stream_stop_required = True
            self.hue.start_streaming(self.area)
            transport = self.transport_factory(
                bridge_ip=self.hue.bridge_ip,
                application_id=application_id,
                client_key=self.client_key,
            )
            transport.start()

            self.state = LifecycleState.STREAMING
            self.ready.set()
            last_good_frame = time.monotonic()
            while not self._stop_requested.is_set():
                if self.capture.apply_requested_reset():
                    frame = self.capture.read()
                    analyzer = make_analyzer(frame)
                    last_good_frame = time.monotonic()
                colors = analyzer.colors(frame)
                transport.send(builder.build(colors))
                try:
                    frame = self.capture.read()
                    last_good_frame = time.monotonic()
                except HarmonizeError:
                    if self.auto_restart_seconds > 0:
                        if (
                            time.monotonic() - last_good_frame
                            >= self.auto_restart_seconds
                        ):
                            self.capture.reset()
                            frame = self.capture.read()
                            analyzer = make_analyzer(frame)
                            last_good_frame = time.monotonic()
                        else:
                            self._stop_requested.wait(1.0)
                        continue
                    raise
                self._stop_requested.wait(self.update_interval_seconds)
        except Exception as exc:
            self.error = exc
            self.state = LifecycleState.ERROR
            self.ready.set()
        finally:
            if self.state is not LifecycleState.ERROR:
                self.state = LifecycleState.STOPPING
            if transport is not None:
                try:
                    transport.close()
                except Exception as cleanup_error:
                    remember_cleanup_error(cleanup_error)
            try:
                self.capture.close()
            except Exception as cleanup_error:
                remember_cleanup_error(cleanup_error)
            if stream_stop_required:
                try:
                    self.hue.stop_streaming(self.area)
                except Exception as cleanup_error:
                    remember_cleanup_error(cleanup_error)
            if self.state is not LifecycleState.ERROR:
                self.state = LifecycleState.IDLE
            self.ready.set()
            self.finished.set()
