import importlib.metadata

from ._black_split import FfmpegBlackSplit, OpenPeriod, Period

__version__ = importlib.metadata.version("ffmpeg_black_split")

__all__ = ["FfmpegBlackSplit", "Period", "OpenPeriod"]
