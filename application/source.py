from typing import Protocol, runtime_checkable
import numpy as np

@runtime_checkable
class Source(Protocol):
    """
    Protocol which returns frames to the frame grabber
    """
    fps: int

    # def __init__(self) -> None: 
    #     super().__init__()

    def open(self) -> None: ...

    def read(self) -> np.ndarray | None: ...

    def close(self) -> None: ...
  