from typing import Protocol, runtime_checkable
import numpy as np


@runtime_checkable
class Source(Protocol):
    """
    Протокол источника, который возвращает кадры для frame grabber
    """

    fps: int

    def open(self) -> None:
        """Открыть базовый источник данных."""
        ...

    def read(self) -> np.ndarray | None:
        """Считать и вернуть следующий кадр."""
        ...

    def close(self) -> None:
        """Освободить ресурсы, принадлежащие источнику."""
        ...
