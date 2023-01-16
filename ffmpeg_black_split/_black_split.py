from __future__ import annotations

import logging
import os
import re
import shlex
import sys
from typing import Literal, TypedDict, Union

from ffmpeg_progress_yield import FfmpegProgress
from tqdm import tqdm

logger = logging.getLogger("ffmpeg-black-split")


class Period(TypedDict):
    """
    Period of time in seconds.
    """

    start: float
    """Start time of the period in seconds."""
    end: float
    """End time of the period in seconds."""
    duration: float
    """Duration of the period in seconds."""


class OpenPeriod(TypedDict):
    start: float
    """Start time of the period in seconds."""
    end: Union[float, None]
    """End time of the period in seconds."""


class FfmpegBlackSplit:
    DEFAULT_BLACK_MIN_DURATION = 2.0
    DEFAULT_PICTURE_BLACK_RATIO_TH = 0.98
    DEFAULT_PIXEL_BLACK_TH = 0.10

    def __init__(self, input_file: str, progress: bool = False):
        """
        Args:
            input_file (str): Input file.
            progress (bool, optional): Show progress bar. Defaults to False.
        """
        self.input_file = input_file
        self.black_periods: list[Period] = []
        self.content_periods: list[Union[Period, OpenPeriod]] = []

        self.progress = progress

    def detect_black_periods(
        self,
        black_min_duration=DEFAULT_BLACK_MIN_DURATION,
        picture_black_ratio_th=DEFAULT_PICTURE_BLACK_RATIO_TH,
        pixel_black_th=DEFAULT_PIXEL_BLACK_TH,
    ) -> list:
        """
        Get black periods from ffmpeg.

        Args:
            black_min_duration (float, optional): Set the minimum detected black duration expressed in seconds.
                                                  It must be a non-negative floating point number.
            picture_black_ratio_th (float, optional): Set the threshold for considering a picture 'black'.
            pixel_black_th (float, optional): Set the threshold for considering a pixel 'black'.

        Returns:
            list: List of black periods.
        """
        black_periods: list[Period] = []

        blackdetect_option_pairs = {
            "black_min_duration": black_min_duration,
            "picture_black_ratio_th": picture_black_ratio_th,
            "pixel_black_th": pixel_black_th,
        }

        blackdetect_options = [
            f"{key}={value}" for key, value in blackdetect_option_pairs.items()
        ]

        try:

            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-i",
                self.input_file,
                "-vf",
                f"blackdetect={':'.join(blackdetect_options)}",
                "-an",
                "-f",
                "null",
                "-",
            ]

            cmd_q = " ".join([shlex.quote(c) for c in cmd])
            logger.debug("Running ffmpeg command: {}".format(cmd_q))

            ff = FfmpegProgress(cmd)
            if self.progress:
                with tqdm(total=100, position=1) as pbar:
                    for p in ff.run_command_with_progress():
                        pbar.update(p - pbar.n)
            else:
                for _ in ff.run_command_with_progress():
                    pass

            if ff.stderr is None:
                raise Exception("No stderr from ffmpeg")

            blackdetect_lines = [
                line
                for line in ff.stderr.splitlines()
                if line.startswith("[blackdetect")
            ]

            if len(blackdetect_lines) == 0:
                print("No black periods detected.", file=sys.stderr)
                return black_periods

            for line in blackdetect_lines:
                # [blackdetect @ 0x137f36f30] black_start:20 black_end:24.96 black_duration:4.96
                #
                # extract the black_start, black_end and black_duration values
                black_start: Union[float, None] = None
                black_end: Union[float, None] = None
                black_duration: Union[float, None] = None
                if black_start_match := re.search(r"black_start:(\d+[\.\d+]?)", line):
                    black_start = float(black_start_match.group(1))
                if black_end_match := re.search(r"black_end:(\d+[\.\d+]?)", line):
                    black_end = float(black_end_match.group(1))
                if black_duration_match := re.search(
                    r"black_duration:(\d+[\.\d+]?)", line
                ):
                    black_duration = float(black_duration_match.group(1))

                if black_start is None or black_end is None or black_duration is None:
                    raise Exception("Could not parse blackdetect line: {}".format(line))

                black_periods.append(
                    {
                        "start": black_start,
                        "end": black_end,
                        "duration": black_duration,
                    }
                )

        except Exception as e:
            raise e

        self.black_periods = black_periods
        self.content_periods = FfmpegBlackSplit.black_periods_to_content_periods(
            self.black_periods
        )
        return self.black_periods

    @staticmethod
    def black_periods_to_content_periods(
        black_periods: list[Period],
    ) -> list[Union[Period, OpenPeriod]]:
        """
        Calculate the inverted black periods to get the content periods.

        Args:
            black_periods (list): List of black periods.

        Returns:
            list: List of content periods.
        """
        content_periods: list[Union[Period, OpenPeriod]] = []
        previous_period_end: float = 0.0
        for black_period in black_periods:
            if black_period["start"] == 0:
                # first black period starts at 0, so we don't need to split it
                previous_period_end = black_period["end"]
                continue

            current_period: OpenPeriod = {
                "start": previous_period_end,
                "end": black_period["start"],
            }
            content_periods.append(current_period)
            previous_period_end = black_period["end"]

        # add a final, open-ended one
        open_period: OpenPeriod = {"start": previous_period_end, "end": None}
        content_periods.append(open_period)

        return content_periods

    def cut_all_periods(
        self,
        output_directory: str,
        no_copy: bool = False,
        progress: bool = False,
    ):
        """
        Cut all periods to individual files.

        Args:
            output_directory (str): Output directory.
            no_copy (bool, optional): Do not copy the streams, reencode them. Defaults to False.
            progress (bool, optional): Show progress bar. Defaults to False.
        """
        if len(self.content_periods) == 0:
            raise Exception("No content periods detected.")

        for content_period in self.content_periods:
            FfmpegBlackSplit.cut_part_from_file(
                self.input_file,
                output_directory=output_directory,
                start=content_period["start"],
                end=content_period.get("end"),
                no_copy=no_copy,
                progress=progress,
            )

    @staticmethod
    def cut_part_from_file(
        input_file: str,
        output_directory: str,
        start: Union[float, None] = None,
        end: Union[float, None, Literal[""]] = None,
        no_copy: bool = False,
        progress: bool = False,
    ):
        """
        Cut a part of a video.

        Args:
            input_file (str): Input file.
            output_directory (str): Output directory.
            start (Union[float, None], optional): Start time. Defaults to None.
            end (Union[float, None, Literal[""]], optional): End time. Defaults to None.
            no_copy (bool, optional): Do not copy the streams, reencode them. Defaults to False.
            progress (bool, optional): Show progress bar. Defaults to False.
        """
        if start is None:
            start = 0

        if end is not None and end != "":
            to_args = ["-t", str(end - start)]
        else:
            end = ""
            to_args = []

        if no_copy:
            codec_args = ["-c:v", "libx264", "-c:a", "aac"]
        else:
            codec_args = ["-c", "copy"]

        suffix = f"{start}-{end}.mkv"
        prefix = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_directory, f"{prefix}_{suffix}")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-ss",
            str(start),
            "-i",
            input_file,
            *to_args,
            *codec_args,
            "-map",
            "0",
            output_file,
        ]

        cmd_q = " ".join([shlex.quote(c) for c in cmd])
        logger.debug("Running ffmpeg command: {}".format(cmd_q))

        ff = FfmpegProgress(cmd)
        if progress:
            with tqdm(total=100, position=1) as pbar:
                for p in ff.run_command_with_progress():
                    pbar.update(p - pbar.n)
        else:
            for _ in ff.run_command_with_progress():
                pass
