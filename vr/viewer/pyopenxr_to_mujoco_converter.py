"""Converts vectors and quaternions from pyopenxr to mujoco space."""
import numpy as np
import xr
from pyquaternion import Quaternion
from xr import Vector3f, Quaternionf


def vector_from_pyopenxr(xr_vector: [Vector3f, np.array]) -> np.ndarray:
    """Convert pyopenxr vector to mujoco space.

    To convert from pyopenxr to mujoco, a 90-degree rotation along the X-axis
    has to be applied, i.e., multiplication by the following offset matrix:

    | 1 0  0 |
    | 0 0 -1 |
    | 0 1  0 |

    mujoco_vector = [xr_vector[0], -xr_vector[2], xr_vector[1]]
    """
    if isinstance(xr_vector, Vector3f):
        xr_vector = xr_vector.as_numpy()
    return np.array([xr_vector[0], -xr_vector[2], xr_vector[1]])


def quaternion_from_pyopenxr(xr_quaternion: Quaternionf) -> np.ndarray:
    """Convert pyopenxr quaternion to mujoco space."""
    xr_quaternion = Quaternion(
        xr_quaternion.w, xr_quaternion.x, xr_quaternion.y, xr_quaternion.z
    )
    xr_quaternion = Quaternion(axis=[1, 0, 0], degrees=90).rotate(xr_quaternion)
    return xr_quaternion.elements


def pyquaternion_from_pyopenxr(xr_quaternion: Quaternionf) -> Quaternion:
    """Convert pyopenxr quaternion to a pyquaternion in mujoco space."""
    return Quaternion(quaternion_from_pyopenxr(xr_quaternion))


def pyquaternion_from_space_offset(offset: xr.Posef) -> Quaternion:
    """Get the calibration quaternion stored in a Posef offset."""
    orientation = offset.orientation
    return Quaternion(orientation.w, orientation.x, orientation.y, orientation.z)


def apply_space_offset_to_pose(
    position: np.ndarray, orientation: Quaternion, offset: xr.Posef
) -> tuple[np.ndarray, Quaternion]:
    """Apply the VR calibration transform to a pose in mujoco space."""
    offset_quaternion = pyquaternion_from_space_offset(offset)
    calibrated_position = offset_quaternion.rotate(position) + offset.position.as_numpy()
    calibrated_orientation = offset_quaternion * orientation
    return calibrated_position, calibrated_orientation


def camera_axes_from_quaternion(
    quaternion: Quaternion,
) -> tuple[np.ndarray, np.ndarray]:
    """Get mujoco forward and up axes for a camera orientation."""
    forward = quaternion.rotate(np.array([0, 1, 0]))
    up = quaternion.rotate(np.array([0, 0, 1]))
    return np.array(forward), np.array(up)


def camera_axes_from_pyopenxr(
    xr_quaternion: Quaternionf,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert pyopenxr quaternion to mujoco forward and up axes."""
    return camera_axes_from_quaternion(pyquaternion_from_pyopenxr(xr_quaternion))
