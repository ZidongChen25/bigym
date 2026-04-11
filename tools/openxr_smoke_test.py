"""Staged OpenXR smoke test for isolating VR startup failures.

This script is intentionally conservative by default:

- `instance`: loader and runtime discovery only
- `system`: instance + HMD system query
- `opengl`: instance + system + OpenGL requirements query
- `context`: dangerous; enters the full pyopenxr OpenGL/session path

The existing BiGym VR recorder goes straight into the `context` stage.
On this machine, that path is currently capable of locking the NVIDIA GPU,
so the default phase stops at `system`.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import sys
import time
from pathlib import Path

import xr


PHASE_ORDER = {
    "instance": 1,
    "system": 2,
    "opengl": 3,
    "context": 4,
}


def log(message: str) -> None:
    """Print a progress line immediately."""
    print(message, flush=True)


def decode_bytes(value: bytes | bytearray | object) -> str:
    """Decode fixed-size C strings from pyopenxr structs."""
    if isinstance(value, (bytes, bytearray)):
        return value.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    return str(value)


def scalar_value(value: object) -> int | object:
    """Extract a Python scalar from ctypes scalar-like values."""
    return getattr(value, "value", value)


def enum_name(value: object) -> str:
    """Return a readable enum name when available."""
    return getattr(value, "name", str(value))


def read_active_runtime() -> dict[str, object] | None:
    """Read the active OpenXR runtime manifest if present."""
    runtime_override = os.environ.get("XR_RUNTIME_JSON")
    if runtime_override:
        runtime_path = Path(runtime_override).expanduser()
    else:
        runtime_path = Path.home() / ".config/openxr/1/active_runtime.json"

    if not runtime_path.exists():
        return None

    with runtime_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    data["_path"] = str(runtime_path)
    return data


def print_environment() -> None:
    """Print the execution environment before touching OpenXR."""
    runtime_info = read_active_runtime()

    log("== Environment ==")
    log(f"python: {sys.executable}")
    log(f"pyopenxr: {xr.__version__}")
    log(f"platform: {platform.platform()}")
    log(f"DISPLAY: {os.environ.get('DISPLAY', '<unset>')}")
    log(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', '<unset>')}")
    log(f"XR_RUNTIME_JSON: {os.environ.get('XR_RUNTIME_JSON', '<unset>')}")
    if runtime_info is None:
        log("active_runtime: <missing>")
    else:
        runtime_name = runtime_info.get("runtime", {}).get("name", "<unknown>")
        runtime_library = runtime_info.get("runtime", {}).get("library_path", "<unknown>")
        log(f"active_runtime: {runtime_name}")
        log(f"active_runtime_manifest: {runtime_info.get('_path')}")
        log(f"active_runtime_library: {runtime_library}")
    log("")


def print_runtime_unavailable_hint() -> None:
    """Print a focused hint for the most common local failure mode."""
    log("hint: the OpenXR loader could not reach a live runtime")
    log("hint: for WiVRn/Monado, make sure the WiVRn server is running on the host and the headset is connected")
    log("hint: if you are testing from a different shell or sandbox, the user runtime socket may also be inaccessible")
    log("")


def get_available_extensions() -> list[str]:
    """Return the available loader/runtime extension names."""
    props = xr.enumerate_instance_extension_properties()
    return sorted(decode_bytes(prop.extension_name) for prop in props)


def build_instance_create_info(enable_opengl: bool) -> xr.InstanceCreateInfo:
    """Build a deterministic instance create info for smoke testing."""
    enabled_extensions: list[str] = []
    if enable_opengl:
        enabled_extensions.append(xr.KHR_OPENGL_ENABLE_EXTENSION_NAME)

    return xr.InstanceCreateInfo(
        application_info=xr.ApplicationInfo(application_name="openxr_smoke_test.py"),
        enabled_extension_names=enabled_extensions,
    )


def print_instance_details(instance: xr.Instance) -> None:
    """Print runtime details for a created instance."""
    props = xr.get_instance_properties(instance)
    log("== Instance ==")
    log(f"runtime_name: {decode_bytes(props.runtime_name)}")
    log(f"runtime_version: {props.runtime_version}")
    log("")


def print_system_details(instance: xr.Instance) -> xr.SystemId:
    """Query and print HMD system details."""
    system_id = xr.get_system(
        instance=instance,
        get_info=xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY),
    )
    props = xr.get_system_properties(instance, system_id)

    log("== System ==")
    log(f"system_id: {scalar_value(system_id)}")
    log(f"system_name: {decode_bytes(props.system_name)}")
    log(f"vendor_id: {props.vendor_id}")
    log(
        "tracking: "
        f"orientation={bool(props.tracking_properties.orientation_tracking)} "
        f"position={bool(props.tracking_properties.position_tracking)}"
    )
    log(
        "graphics_limits: "
        f"max_width={props.graphics_properties.max_swapchain_image_width} "
        f"max_height={props.graphics_properties.max_swapchain_image_height} "
        f"max_layers={props.graphics_properties.max_layer_count}"
    )
    log("")

    return system_id


def print_opengl_requirements(instance: xr.Instance, system_id: xr.SystemId) -> None:
    """Query OpenGL graphics requirements without creating a GL context."""
    if platform.system() == "Linux":
        from xr.platform.linux import (
            GraphicsRequirementsOpenGLKHR,
            PFN_xrGetOpenGLGraphicsRequirementsKHR,
        )
    elif platform.system() == "Windows":
        from xr.platform.windows import (
            GraphicsRequirementsOpenGLKHR,
            PFN_xrGetOpenGLGraphicsRequirementsKHR,
        )
    else:
        raise RuntimeError(f"OpenGL smoke test is not implemented on {platform.system()}")

    proc = xr.get_instance_proc_addr(instance, "xrGetOpenGLGraphicsRequirementsKHR")
    if not proc:
        raise RuntimeError("xrGetOpenGLGraphicsRequirementsKHR is unavailable")

    get_requirements = ctypes.cast(proc, PFN_xrGetOpenGLGraphicsRequirementsKHR)
    requirements = GraphicsRequirementsOpenGLKHR()
    result = get_requirements(instance, system_id, ctypes.byref(requirements))
    result = xr.check_result(xr.Result(result))
    if result.is_exception():
        raise result

    log("== OpenGL Requirements ==")
    log(f"min_api_version_supported: {requirements.min_api_version_supported}")
    log(f"max_api_version_supported: {requirements.max_api_version_supported}")
    log("")


def run_dangerous_context_stage(
    idle_seconds: float = 0.0,
    frame_seconds: float = 0.0,
) -> None:
    """Enter the full XRContextObject path.

    This stage creates a hidden GLFW window, OpenGL context, session,
    reference space, and swapchains. It is intentionally isolated because
    this is the stage that currently appears to hard-lock the GPU on the
    user's machine.
    """
    from vr.viewer.xr_context import XRContextObject

    log("== Context ==")
    log(
        "WARNING: entering XRContextObject; this is the same OpenGL/session path used by the VR recorder."
    )
    with XRContextObject(
        instance_create_info=build_instance_create_info(enable_opengl=True),
    ) as context:
        log(f"context.instance: {context.instance}")
        log(f"context.system_id: {scalar_value(context.system_id)}")
        log(f"context.session: {context.session}")
        if idle_seconds > 0:
            deadline = time.monotonic() + idle_seconds
            last_state = None
            log(f"context idle polling for {idle_seconds:.1f}s")
            while time.monotonic() < deadline:
                context.poll_xr_events()
                if context.session_state != last_state:
                    log(f"context.session_state: {enum_name(context.session_state)}")
                    last_state = context.session_state
                time.sleep(0.1)
            log("context idle polling finished")
        if frame_seconds > 0:
            deadline = time.monotonic() + frame_seconds
            frames = 0
            last_log = time.monotonic()
            log(f"context frame loop for {frame_seconds:.1f}s")
            for _frame_state in context.frame_loop():
                frames += 1
                now = time.monotonic()
                if now - last_log >= 1.0:
                    log(f"context.frames: {frames}")
                    last_log = now
                if now >= deadline:
                    break
            log(f"context frame loop finished after {frames} frames")
        log("context stage reached successfully")
    log("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=tuple(PHASE_ORDER),
        default="system",
        help="Run all stages up to and including this phase.",
    )
    parser.add_argument(
        "--context-idle-seconds",
        type=float,
        default=0.0,
        help="When using --phase context, keep the XR session alive and only poll events for this many seconds.",
    )
    parser.add_argument(
        "--context-frame-seconds",
        type=float,
        default=0.0,
        help="When using --phase context, run the OpenXR frame loop without MuJoCo rendering for this many seconds.",
    )
    args = parser.parse_args()

    print_environment()

    available_extensions = get_available_extensions()
    log("== Loader Extensions ==")
    log(f"extension_count: {len(available_extensions)}")
    log(
        "supports_khr_opengl_enable: "
        f"{xr.KHR_OPENGL_ENABLE_EXTENSION_NAME in available_extensions}"
    )
    log("")

    needs_opengl = PHASE_ORDER[args.phase] >= PHASE_ORDER["opengl"]
    if needs_opengl and xr.KHR_OPENGL_ENABLE_EXTENSION_NAME not in available_extensions:
        raise RuntimeError(
            f"Requested --phase {args.phase}, but {xr.KHR_OPENGL_ENABLE_EXTENSION_NAME} "
            "is not exposed by the current runtime."
        )

    try:
        instance = None
        try:
            log("stage: create_instance")
            instance = xr.create_instance(
                build_instance_create_info(enable_opengl=needs_opengl)
            )
            print_instance_details(instance)

            if PHASE_ORDER[args.phase] >= PHASE_ORDER["system"]:
                log("stage: get_system")
                system_id = print_system_details(instance)
            else:
                system_id = None

            if PHASE_ORDER[args.phase] >= PHASE_ORDER["opengl"]:
                log("stage: get_opengl_graphics_requirements")
                print_opengl_requirements(instance, system_id)
        finally:
            if instance is not None:
                log("stage: destroy_instance")
                xr.destroy_instance(instance)
                log("")

        if PHASE_ORDER[args.phase] >= PHASE_ORDER["context"]:
            run_dangerous_context_stage(
                idle_seconds=args.context_idle_seconds,
                frame_seconds=args.context_frame_seconds,
            )

        log(f"success: completed through phase '{args.phase}'")
        return 0
    except xr.RuntimeUnavailableError as exc:
        log(f"failure: {exc.__class__.__name__}: {exc}")
        print_runtime_unavailable_hint()
        return 2
    except xr.XrException as exc:
        log(f"failure: {exc.__class__.__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
