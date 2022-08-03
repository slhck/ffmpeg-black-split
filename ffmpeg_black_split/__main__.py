#!/usr/bin/env python3
#
# Cut a video by black frames.
#
# Author: Werner Robitza
# License: MIT

import argparse
import os
import json
import sys
import tempfile
import re
import shlex
from tqdm import tqdm
from ffmpeg_progress_yield import FfmpegProgress

from .__init__ import __version__ as version


DEFAULT_BLACK_MIN_DURATION = 2.0
DEFAULT_PICTURE_BLACK_RATIO_TH = 0.98
DEFAULT_PIXEL_BLACK_TH = 0.10


def get_black_periods(
    in_f,
    black_min_duration=DEFAULT_BLACK_MIN_DURATION,
    picture_black_ratio_th=DEFAULT_PICTURE_BLACK_RATIO_TH,
    pixel_black_th=DEFAULT_PIXEL_BLACK_TH,
    progress=False,
    verbose=False,
):
    """
    Get black periods from ffmpeg
    """
    black_periods = []

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
            in_f,
            "-vf",
            f"blackdetect={':'.join(blackdetect_options)}",
            "-an",
            "-f",
            "null",
            "-",
        ]

        if verbose:
            cmd_q = " ".join([shlex.quote(c) for c in cmd])
            print("Running ffmpeg command: {}".format(cmd_q), file=sys.stderr)

        ff = FfmpegProgress(cmd)
        if progress:
            with tqdm(total=100, position=1) as pbar:
                for progress in ff.run_command_with_progress():
                    pbar.update(progress - pbar.n)
        else:
            for _ in ff.run_command_with_progress():
                pass

        blackdetect_lines = [
            line for line in ff.stderr.splitlines() if line.startswith("[blackdetect")
        ]

        if len(blackdetect_lines) == 0:
            print("No black periods detected.", file=sys.stderr)
            return black_periods

        for line in blackdetect_lines:
            # [blackdetect @ 0x137f36f30] black_start:20 black_end:24.96 black_duration:4.96
            #
            # extract the black_start, black_end and black_duration values
            black_start = float(re.search(r"black_start:(\d+[\.\d+]?)", line).group(1))
            black_end = float(re.search(r"black_end:(\d+[\.\d+]?)", line).group(1))
            black_duration = float(
                re.search(r"black_duration:(\d+[\.\d+]?)", line).group(1)
            )

            black_periods.append(
                {
                    "start": black_start,
                    "end": black_end,
                    "duration": black_duration,
                }
            )

    except Exception as e:
        raise e

    return black_periods


def black_periods_to_content_periods(black_periods):
    """
    Get the inverted black periods to cut the segments.
    """
    content_periods = []
    previous_period_end = 0
    for black_period in black_periods:
        if black_period["start"] == 0:
            # first black period starts at 0, so we don't need to split it
            previous_period_end = black_period["end"]
            continue

        current_period = {
            "start": previous_period_end,
            "end": black_period["start"],
        }
        content_periods.append(current_period)
        previous_period_end = black_period["end"]

    # add a final, open-ended one
    content_periods.append({"start": previous_period_end})

    return content_periods


def cut_part(
    input_file,
    output_directory=None,
    start=None,
    end=None,
    no_copy=False,
    progress=False,
    verbose=False,
):
    """
    Cut a part of a video.
    """
    if output_directory is None:
        output_directory = os.getcwd()

    if start is None:
        start = 0

    if end is not None:
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

    if verbose:
        cmd_q = " ".join([shlex.quote(c) for c in cmd])
        print("Running ffmpeg command: {}".format(cmd_q), file=sys.stderr)

    ff = FfmpegProgress(cmd)
    if progress:
        with tqdm(total=100, position=1) as pbar:
            for progress in ff.run_command_with_progress():
                pbar.update(progress - pbar.n)
    else:
        for _ in ff.run_command_with_progress():
            pass


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
        "--no-split", action="store_true", help="Don't split the video into segments."
    )
    parser.add_argument(
        "--no-copy", action="store_true", help="Don't stream-copy, but re-encode the video."
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

    cli_args = parser.parse_args()

    black_periods = get_black_periods(
        cli_args.input,
        cli_args.black_min_duration,
        cli_args.picture_black_ratio_th,
        cli_args.pixel_black_th,
        progress=cli_args.progress,
        verbose=cli_args.verbose,
    )

    if not len(black_periods):
        print("No black periods detected, nothing to split.", file=sys.stderr)
        return 1

    content_periods = black_periods_to_content_periods(black_periods)

    if cli_args.verbose:
        print("Black and content periods detected:", file=sys.stderr)
        print(
            json.dumps(
                {
                    "black_periods": black_periods,
                    "content_periods": content_periods,
                },
                indent=2,
            )
        )

    if not cli_args.no_split:
        # cut the individual periods to files
        for content_period in content_periods:
            cut_part(
                cli_args.input,
                output_directory=cli_args.output_directory,
                start=content_period["start"],
                end=content_period.get("end"),
                no_copy=cli_args.no_copy,
                progress=cli_args.progress,
                verbose=cli_args.verbose,
            )


if __name__ == "__main__":
    main()
