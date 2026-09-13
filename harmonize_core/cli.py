"""Legacy-compatible manual CLI backed by the refactored components."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

from termcolor import colored

from harmonize_config import ConfigError, HarmonizeConfig, load_config, load_credentials

from .capture import CaptureSource
from .controller import HarmonizeController, LifecycleState
from .errors import HarmonizeError
from .hue import (
    HueBridge,
    discover_bridge,
    resolve_area_name,
    resolve_group_id,
    select_area_interactively,
)


@dataclass(frozen=True)
class RuntimeOptions:
    bridge_ip: str | None
    credentials_file: Path
    entertainment_area: str | None
    capture_device: int
    capture_backend: str
    stream_source: str | None
    startup_wait_seconds: float
    brightness_adjustment: int
    auto_restart_seconds: float
    single_light: bool
    sample_breadth: float
    update_interval_seconds: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-g", "--groupid")
    parser.add_argument("-b", "--bridgeid")
    parser.add_argument("-i", "--bridgeip")
    parser.add_argument("-s", "--single_light", action="store_true")
    parser.add_argument(
        "-w", "--video_wait_time", type=float, default=None
    )
    parser.add_argument("-f", "--stream_filename")
    parser.add_argument("-l", "--light_brightness", type=int, default=None)
    parser.add_argument("-a", "--auto_restart", type=float, default=None)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="require deterministic configuration and prohibit prompts",
    )
    parser.add_argument(
        "--check-area",
        action="store_true",
        help="resolve the selected Hue area read-only, then exit",
    )
    return parser


def _load_optional_config(args: argparse.Namespace) -> HarmonizeConfig | None:
    path = args.config
    if path is None and Path("harmonize.toml").is_file():
        path = Path("harmonize.toml")
    if path is None:
        if args.unattended:
            raise ConfigError(
                "--unattended requires --config or an existing harmonize.toml"
            )
        return None
    return load_config(path, unattended=args.unattended)


def _runtime_options(
    args: argparse.Namespace, config: HarmonizeConfig | None
) -> RuntimeOptions:
    if config is None:
        return RuntimeOptions(
            bridge_ip=args.bridgeip,
            credentials_file=Path("client.json").resolve(),
            entertainment_area=None,
            capture_device=0,
            capture_backend="gstreamer",
            stream_source=args.stream_filename,
            startup_wait_seconds=(
                5.0 if args.video_wait_time is None else args.video_wait_time
            ),
            brightness_adjustment=(
                30 if args.light_brightness is None else args.light_brightness
            ),
            auto_restart_seconds=(
                0.0 if args.auto_restart is None else args.auto_restart
            ),
            single_light=args.single_light,
            sample_breadth=0.15,
            update_interval_seconds=0.0167,
        )

    return RuntimeOptions(
        bridge_ip=args.bridgeip or config.hue.bridge_ip,
        credentials_file=config.hue.credentials_file,
        entertainment_area=config.hue.entertainment_area,
        capture_device=config.capture.device_index,
        capture_backend=config.capture.backend,
        stream_source=args.stream_filename or config.capture.stream_source,
        startup_wait_seconds=(
            config.ambilight.video_wait_seconds
            if args.video_wait_time is None
            else args.video_wait_time
        ),
        brightness_adjustment=(
            config.ambilight.brightness_adjustment
            if args.light_brightness is None
            else args.light_brightness
        ),
        auto_restart_seconds=(
            config.ambilight.auto_restart_seconds
            if args.auto_restart is None
            else args.auto_restart
        ),
        single_light=args.single_light or config.ambilight.single_light,
        sample_breadth=config.ambilight.sample_breadth,
        update_interval_seconds=config.ambilight.update_interval_seconds,
    )


def _resolve_bridge(args: argparse.Namespace, options: RuntimeOptions) -> str:
    if args.bridgeid and not options.bridge_ip:
        raise HarmonizeError(
            "--bridgeid cannot select an mDNS address deterministically; "
            "also provide --bridgeip"
        )
    return options.bridge_ip or discover_bridge()


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = _load_optional_config(args)
        options = _runtime_options(args, config)
        credentials = load_credentials(
            options.credentials_file, unattended=args.unattended
        )
        for warning in credentials.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        bridge_ip = _resolve_bridge(args, options)
        if args.verbose:
            print(f"INFO: Hue bridge selected at {bridge_ip}")
        hue = HueBridge(bridge_ip, credentials.username)
        resources = hue.list_entertainment_resources()
        if options.entertainment_area is not None:
            area = resolve_area_name(resources, options.entertainment_area)
        elif args.groupid is not None:
            area = resolve_group_id(resources, args.groupid)
        elif args.unattended:
            raise HarmonizeError(
                "Unattended mode requires hue.entertainment_area"
            )
        else:
            area = select_area_interactively(resources)

        print(
            f'Using Hue Entertainment area "{area.name}" '
            f"(legacy group {area.legacy_group_id}, {len(area.channels)} channels)"
        )
        if args.check_area:
            print("Read-only area resolution succeeded; streaming was not started.")
            return 0

        print(colored("--- Starting Harmonize Project ---", "green"))
        capture = CaptureSource(
            device_index=options.capture_device,
            backend=options.capture_backend,
            stream_source=options.stream_source,
        )
        controller = HarmonizeController(
            hue=hue,
            area=area,
            capture=capture,
            client_key=credentials.clientkey,
            brightness_adjustment=options.brightness_adjustment,
            sample_breadth=options.sample_breadth,
            update_interval_seconds=options.update_interval_seconds,
            single_light=options.single_light,
            auto_restart_seconds=options.auto_restart_seconds,
        )
        controller.start_background()
        if not controller.ready.wait(max(0.1, options.startup_wait_seconds)):
            controller.request_stop()
            controller.join()
            raise HarmonizeError(
                "Controller did not become ready within "
                f"{options.startup_wait_seconds:g} seconds"
            )
        if controller.error is not None:
            controller.join()
            raise HarmonizeError(str(controller.error))
        print("Hue Entertainment streaming is ready.")
        while not controller.finished.is_set():
            command = input(
                "Please r to reset the video capture, q to stop streaming, "
                "followed by Enter: "
            ).strip()
            if command == "r":
                controller.request_capture_reset()
            elif command == "q":
                controller.request_stop()
                controller.join()
                break
        controller.join()
        if controller.error is not None:
            raise HarmonizeError(str(controller.error))
        if controller.state is not LifecycleState.IDLE:
            raise HarmonizeError(
                f"Controller stopped in unexpected state {controller.state.value}"
            )
        return 0
    except (ConfigError, HarmonizeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        if "controller" in locals():
            controller.request_stop()
            controller.join()
        return 130
    finally:
        if "hue" in locals():
            hue.close()


def main() -> None:
    raise SystemExit(run())
