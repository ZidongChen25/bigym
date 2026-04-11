"""CLI launcher for the VR viewer without the DearPyGUI recorder window."""

from __future__ import annotations

import argparse
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
        help="BiGym task to launch in VR.",
    )
    parser.add_argument(
        "--control-profile",
        choices=sorted(CONTROL_PROFILES),
        default="H1 Upper Body Floating",
        help="VR control profile.",
    )
    parser.add_argument(
        "--robot",
        choices=sorted(ROBOTS),
        default="Default",
        help="Robot model override.",
    )
    parser.add_argument(
        "--floating-dofs",
        nargs="+",
        choices=[dof.name for dof in PelvisDof],
        default=["X", "Y", "RZ"],
        help="Floating base DOFs to enable.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "demo",
        help="Directory to save recorded demos to.",
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
    viewer.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
