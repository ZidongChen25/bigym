"""VR Demo Recorder."""

from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.demo_recorder.demo_recorder_window import DemoRecorderWindow
from tools.shared.primary_window import PrimaryWindow


class DemoRecorder:
    """VR Demo Recorder."""

    def __init__(self):
        """Init."""
        PrimaryWindow(
            DemoRecorderWindow,
            title="VR Demo Recorder",
            height=450,
            resizable=True,
        )


if __name__ == "__main__":
    DemoRecorder()
