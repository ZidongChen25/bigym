"""Abstract base class for defining control profiles."""
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from gymnasium.core import ActType
from pyquaternion import Quaternion
from xr import Posef

from bigym.bigym_env import BiGymEnv
from vr.viewer import Side
from vr.viewer.pyopenxr_to_mujoco_converter import (
    apply_space_offset_to_pose,
    pyquaternion_from_pyopenxr,
    vector_from_pyopenxr,
)
from vr.viewer.xr_context import XRContextObject


class ControlProfile(ABC):
    """Abstract base class for defining control profiles."""

    def __init__(self, env: BiGymEnv):
        """Init."""
        self._env = env

    @abstractmethod
    def get_next_action(
        self,
        context: XRContextObject,
        steps_count: int,
        space_offset: Posef,
    ) -> ActType:
        """Get the next action.

        :param context: XR context object to access current input.
        :param steps_count: Amount of physical steps to be taken.
            Divide delta actions by this value in order to keep actions
            consistent regardless of the current frame rate.
        :param space_offset: Virtual space offset.
        """
        pass

    def reset(
        self,
        context: Optional[XRContextObject] = None,
        space_offset: Optional[Posef] = None,
    ):
        """Custom reset behaviour, called on environment reset."""
        pass

    def get_reset_space_offset(self, context: XRContextObject) -> Posef:
        """Get a calibration transform to apply after an environment reset."""
        return Posef()

    @staticmethod
    def _get_controller_pose(
        context: XRContextObject, side: Side, offset: Posef
    ) -> tuple[np.ndarray, Quaternion]:
        pose = context.input.state[side].pose_aim
        pos = vector_from_pyopenxr(pose.position)
        quat = pyquaternion_from_pyopenxr(pose.orientation)
        pos, quat = apply_space_offset_to_pose(pos, quat, offset)
        return pos, quat

    @staticmethod
    def _get_hmd_pose(
        context: XRContextObject, offset: Posef, pivot_offset: np.ndarray = np.zeros(3)
    ) -> tuple[np.ndarray, Quaternion]:
        pose = context.input.hmd_pose
        pos = vector_from_pyopenxr(pose.position)
        quat = pyquaternion_from_pyopenxr(pose.orientation)
        pos, quat = apply_space_offset_to_pose(pos, quat, offset)
        pos += quat.rotate(pivot_offset)
        return pos, quat
