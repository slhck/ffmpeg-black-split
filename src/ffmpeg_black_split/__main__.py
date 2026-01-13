#!/usr/bin/env python3
#
# Cut a video by black frames.
#
# Author: Werner Robitza
# License: MIT

import argparse
import json
import logging
import os
import sys

from .__init__ import __version__ as version
from ._black_split import FfmpegBlackSplit
from ._log import CustomLogFormatter

logger = logging.getLogger("ffmpeg-black-split")


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("ffmpeg-black-split")
    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(level)

    ch.setFormatter(CustomLogFormatter())

    logger.addHandler(ch)

    return logger


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="ffmpeg-black-split v" + version,
    )
    parser.add_argument("input", help="input file")
    parser.add_argument(
        "-d",
        "--black-min-duration",
        type=float,
        default=2.0,
        help="Set the minimum detected black duration expressed in seconds. It must be a non-negative floating point number.",
    )
    parser.add_argument(
        "-r",
        "--picture-black-ratio-th",
        type=float,
        default=0.98,
        help="Set the threshold for considering a picture 'black'",
    )
    parser.add_argument(
        "-t",
        "--pixel-black-th",
        type=float,
        default=0.10,
        help="Set the threshold for considering a pixel 'black'",
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Set the output directory. Default is the current working directory.",
    )
    parser.add_argument(
        "-e",
        "--output-extension",
        default="mkv",
        help="Set the ffmpeg output extension. Default is 'mkv'. Choose 'mov' for QuickTime-compatible files.",
    )
    parser.add_argument(
        "--no-split", action="store_true", help="Don't split the video into segments."
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Don't stream-copy, but re-encode the video. This is useful in case of conversion errors when using different output formats.",
    )
    parser.add_argument(
        "-p", "--progress", action="store_true", help="Show a progress bar on stderr"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose info to stderr, and JSON of black and content periods to stdout",
    )
    parser.add_argument(
        "--ffmpeg-path",
        type=str,
        default="ffmpeg",
        help="Path to ffmpeg executable",
    )

    cli_args = parser.parse_args()

    logger = setup_logger(level=logging.DEBUG if cli_args.verbose else logging.INFO)

    ffbs = FfmpegBlackSplit(
        cli_args.input, progress=cli_args.progress, ffmpeg_path=cli_args.ffmpeg_path
    )

    ffbs.detect_black_periods(
        black_min_duration=cli_args.black_min_duration,
        picture_black_ratio_th=cli_args.picture_black_ratio_th,
        pixel_black_th=cli_args.pixel_black_th,
    )

    if not len(ffbs.black_periods):
        logger.error("No black periods detected, nothing to split.")
        exit(1)

    logger.debug("Black and content periods detected:")
    print(
        json.dumps(
            {
                "black_periods": ffbs.black_periods,
                "content_periods": ffbs.content_periods,
            },
            indent=2,
        )
    )

    if not cli_args.no_split:
        # cut the individual periods to files
        ffbs.cut_all_periods(
            output_directory=(
                cli_args.output_directory if cli_args.output_directory else os.getcwd()
            ),
            extension=cli_args.output_extension,
            no_copy=cli_args.no_copy,
            progress=cli_args.progress,
        )


if __name__ == "__main__":
    main()
