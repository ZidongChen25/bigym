"""Tests for VR reset anchoring semantics."""

from types import SimpleNamespace

import numpy as np
from numpy.testing import assert_allclose
from xr import Posef

from bigym.action_modes import JointPositionActionMode
from bigym.envs.move_plates import MovePlate
from vr.viewer import Side
from vr.viewer.controller import ControllerState
from vr.viewer.control_profiles.h1_floating import H1Floating


def _make_pose(
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    qx: float = 0.0,
    qy: float = 0.0,
    qz: float = 0.0,
    qw: float = 1.0,
) -> Posef:
    pose = Posef()
    pose.position.x = x
    pose.position.y = y
    pose.position.z = z
    pose.orientation.x = qx
    pose.orientation.y = qy
    pose.orientation.z = qz
    pose.orientation.w = qw
    return pose


def _make_context(
    hmd_pose: Posef,
    left_controller_pose: Posef,
    right_controller_pose: Posef,
):
    state = [ControllerState(), ControllerState()]
    state[Side.LEFT].is_active = True
    state[Side.RIGHT].is_active = True
    state[Side.LEFT].pose_aim = left_controller_pose
    state[Side.RIGHT].pose_aim = right_controller_pose
    return SimpleNamespace(
        input=SimpleNamespace(
            hmd_pose=hmd_pose,
            state=state,
        )
    )


def _assert_quaternion_close(actual: np.ndarray, expected: np.ndarray, atol: float = 1e-6):
    if np.allclose(actual, expected, atol=atol):
        return
    assert_allclose(actual, -expected, atol=atol)


def test_h1_floating_reset_keeps_arm_targets_at_reset_pose(monkeypatch):
    env = MovePlate(
        action_mode=JointPositionActionMode(absolute=True, floating_base=True)
    )
    env.reset(seed=7)
    profile = H1Floating(env)

    context = _make_context(
        hmd_pose=_make_pose(x=0.2, y=1.0, z=0.0),
        left_controller_pose=_make_pose(x=0.35, y=1.15, z=-0.2),
        right_controller_pose=_make_pose(x=0.35, y=1.15, z=0.2),
    )

    space_offset = profile.get_reset_space_offset(context)
    profile.reset(context, space_offset)

    captured: dict[str, object] = {}

    def fake_solve(**kwargs):
        captured["left_target"] = kwargs["target_pose_left"]
        captured["right_target"] = kwargs["target_pose_right"]
        return np.concatenate((kwargs["qpos_arm_left"], kwargs["qpos_arm_right"]))

    monkeypatch.setattr(profile._ik, "solve", fake_solve)

    action = profile.get_next_action(context, steps_count=1, space_offset=space_offset)

    base_dofs = env.robot.floating_base.dof_amount
    assert_allclose(action[:base_dofs], np.zeros(base_dofs), atol=1e-6)

    left_anchor = profile._wrist_reset_poses[Side.LEFT]
    right_anchor = profile._wrist_reset_poses[Side.RIGHT]
    assert_allclose(captured["left_target"].position, left_anchor.position, atol=1e-6)
    assert_allclose(captured["right_target"].position, right_anchor.position, atol=1e-6)
    _assert_quaternion_close(
        captured["left_target"].orientation.elements,
        left_anchor.orientation.elements,
    )
    _assert_quaternion_close(
        captured["right_target"].orientation.elements,
        right_anchor.orientation.elements,
    )

    env.close()


def test_h1_floating_reset_applies_controller_motion_relative_to_reset(monkeypatch):
    env = MovePlate(
        action_mode=JointPositionActionMode(absolute=True, floating_base=True)
    )
    env.reset(seed=11)
    profile = H1Floating(env)

    left_controller_pose = _make_pose(x=0.35, y=1.15, z=-0.2)
    right_controller_pose = _make_pose(x=0.35, y=1.15, z=0.2)
    context = _make_context(
        hmd_pose=_make_pose(x=0.1, y=1.0, z=0.0),
        left_controller_pose=left_controller_pose,
        right_controller_pose=right_controller_pose,
    )

    space_offset = profile.get_reset_space_offset(context)
    profile.reset(context, space_offset)

    captured: dict[str, object] = {}

    def fake_solve(**kwargs):
        captured["left_target"] = kwargs["target_pose_left"]
        captured["right_target"] = kwargs["target_pose_right"]
        return np.concatenate((kwargs["qpos_arm_left"], kwargs["qpos_arm_right"]))

    monkeypatch.setattr(profile._ik, "solve", fake_solve)

    context.input.state[Side.LEFT].pose_aim = _make_pose(x=0.45, y=1.15, z=-0.2)
    controller_position, _ = profile._get_controller_pose(
        context, Side.LEFT, space_offset
    )
    controller_anchor = profile._controller_reset_poses[Side.LEFT]
    profile.get_next_action(context, steps_count=1, space_offset=space_offset)

    left_anchor = profile._wrist_reset_poses[Side.LEFT]
    right_anchor = profile._wrist_reset_poses[Side.RIGHT]
    expected_left_position = (
        left_anchor.position + controller_position - controller_anchor.position
    )
    assert_allclose(
        captured["left_target"].position,
        expected_left_position,
        atol=1e-6,
    )
    assert_allclose(captured["right_target"].position, right_anchor.position, atol=1e-6)
    env.close()
