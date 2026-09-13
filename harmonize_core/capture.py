"""Single-owner OpenCV capture with source-preserving reset."""

from __future__ import annotations

import threading
from typing import Any

import cv2

from .errors import HarmonizeError


class CaptureSource:
    """Own one OpenCV VideoCapture; only the controller thread calls methods."""

    def __init__(
        self,
        *,
        device_index: int = 0,
        backend: str = "gstreamer",
        stream_source: str | None = None,
        cv2_module: Any = cv2,
    ):
        self.device_index = device_index
        self.backend = backend
        self.stream_source = stream_source
        self._cv2 = cv2_module
        self._capture = None
        self._reset_requested = threading.Event()

    @property
    def source_description(self) -> str:
        if self.stream_source is not None:
            return self.stream_source
        return f"/dev/video{self.device_index}"

    def _new_capture(self):
        if self.stream_source is not None:
            return self._cv2.VideoCapture(self.stream_source)
        backend_id = {
            "gstreamer": self._cv2.CAP_GSTREAMER,
            "v4l2": self._cv2.CAP_V4L2,
            "any": self._cv2.CAP_ANY,
        }[self.backend]
        return self._cv2.VideoCapture(self.device_index, backend_id)

    def open(self) -> None:
        if self._capture is not None:
            raise HarmonizeError("Capture source is already open")
        capture = self._new_capture()
        if not capture.isOpened():
            capture.release()
            raise HarmonizeError(
                f"Unable to open capture source {self.source_description}"
            )
        capture.set(self._cv2.CAP_PROP_BUFFERSIZE, 0)
        self._capture = capture

    def read(self):
        if self._capture is None:
            raise HarmonizeError("Capture source is not open")
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise HarmonizeError(
                f"Unable to read a frame from {self.source_description}"
            )
        return frame

    def request_reset(self) -> None:
        """Signal reset; the controller owner performs it between reads."""

        self._reset_requested.set()

    def apply_requested_reset(self) -> bool:
        if not self._reset_requested.is_set():
            return False
        self._reset_requested.clear()
        self.reset()
        return True

    def reset(self) -> None:
        self.close()
        self.open()

    def close(self) -> None:
        capture, self._capture = self._capture, None
        if capture is not None:
            capture.release()
