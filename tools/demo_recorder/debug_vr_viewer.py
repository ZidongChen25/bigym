"""Debug launcher for isolating VRViewer subsystems."""

from __future__ import annotations

import argparse
import threading
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bigym.action_modes import JointPositionActionMode, PelvisDof
from tools.shared.utils import CONTROL_PROFILES, ENVIRONMENTS, ROBOTS
from vr.viewer.vr_viewer import VRViewer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--environment",
        choices=sorted(ENVIRONMENTS),
        default="Move Plate",
    )
    parser.add_argument(
        "--control-profile",
        choices=sorted(CONTROL_PROFILES),
        default="H1 Upper Body Floating",
    )
    parser.add_argument(
        "--robot",
        choices=sorted(ROBOTS),
        default="Default",
    )
    parser.add_argument(
        "--floating-dofs",
        nargs="+",
        choices=[dof.name for dof in PelvisDof],
        default=["X", "Y", "RZ"],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "demo",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=10.0,
        help="Stop the viewer after this many seconds.",
    )
    parser.add_argument(
        "--disable-render",
        action="store_true",
        help="Skip VRMujocoRenderer.render().",
    )
    parser.add_argument(
        "--disable-env-step",
        action="store_true",
        help="Skip environment stepping while keeping the XR loop active.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    floating_dofs = [PelvisDof[dof_name] for dof_name in args.floating_dofs]
    viewer = VRViewer(
        env_cls=ENVIRONMENTS[args.environment],
        action_mode=JointPositionActionMode(
            absolute=True,
            floating_base=True,
            floating_dofs=floating_dofs,
        ),
        control_profile_cls=CONTROL_PROFILES[args.control_profile],
        demo_directory=args.output_dir,
        robot_cls=ROBOTS[args.robot],
    )

    if args.disable_render:
        viewer._render_frame = lambda frame_state: None

    if args.disable_env_step:
        viewer._env.step = lambda action, fast=True: ({}, viewer._env.reward, False, False, {})

    exit_event = threading.Event()
    threading.Timer(args.max_seconds, exit_event.set).start()
    viewer.run(exit_event=exit_event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
