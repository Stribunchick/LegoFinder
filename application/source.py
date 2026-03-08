from typing import Protocol
import numpy as np

class Source(Protocol):
    """
    Protocol which returns frames to the frame grabber
    """
    fps: int

    def open(self) -> None: ...

    def read(self) -> np.ndarray | None: ...

    def close(self) -> None: ...

    