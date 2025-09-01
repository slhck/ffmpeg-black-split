#!/usr/bin/env pytest

import json
import os
import subprocess

import pytest

from ffmpeg_black_split import FfmpegBlackSplit as ffbs

TEST_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.mp4"))


def run_command(cmd):
    """
    Run a command directly
    """
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        return stdout.decode("utf-8"), stderr.decode("utf-8")
    else:
        raise RuntimeError(
            "[error] running command {}: {}".format(
                " ".join(cmd), stderr.decode("utf-8")
            )
        )


@pytest.fixture(scope="session")
def clear_files_teardown():
    yield None
    for f in os.listdir(os.path.dirname(TEST_FILE)):
        if f.endswith(".mkv"):
            os.remove(os.path.join(os.path.dirname(TEST_FILE), f))


class TestBlackSplit:
    def test_output(self, clear_files_teardown):
        """
        Test JSON output
        """
        stdout, _ = run_command(
            [
                "python3",
                "-m",
                "ffmpeg_black_split",
                TEST_FILE,
                "-v",
                "-o",
                os.path.dirname(__file__),
                "--no-copy",
            ]
        )

        assert json.loads(stdout) == {
            "black_periods": [
                {"start": 0.0, "end": 5.0, "duration": 5.0},
                {"start": 10.0, "end": 15.0, "duration": 5.0},
                {"start": 20.0, "end": 25.0, "duration": 5.0},
            ],
            "content_periods": [
                {"start": 5.0, "end": 10.0},
                {"start": 15.0, "end": 20.0},
                {"start": 25.0, "end": None},
            ],
        }

        for output_file in [
            "test_5.0-10.0.mkv",
            "test_15.0-20.0.mkv",
            "test_25.0-.mkv",
        ]:
            print(f"Testing {output_file} ... ")

            output_file_path = os.path.join(os.path.dirname(__file__), output_file)
            assert os.path.exists(output_file_path)

            # get the duration of the output via ffmpeg
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                output_file_path,
            ]
            stdout, _ = run_command(cmd)
            assert float(stdout) == 5.0

            os.remove(output_file_path)

    def test_filter_black_periods(self):
        """
        Test the filter_black_periods method
        """
        fbs = ffbs(TEST_FILE)
        black_periods = fbs.detect_black_periods()

        # test with num_cuts=1
        filtered_periods = fbs.filter_black_periods(black_periods, num_cuts=1)
        assert len(filtered_periods) == 1
        assert filtered_periods[0] == {"start": 10.0, "end": 15.0, "duration": 5.0}

        # test with num_cuts=2
        filtered_periods = fbs.filter_black_periods(black_periods, num_cuts=2)
        assert len(filtered_periods) == 2
        assert filtered_periods == [
            {"start": 0.0, "end": 5.0, "duration": 5.0},
            {"start": 20.0, "end": 25.0, "duration": 5.0},
        ]

        # test with num_cuts greater than available periods
        filtered_periods = fbs.filter_black_periods(black_periods, num_cuts=4)
        assert filtered_periods == black_periods

        # test with empty black_periods
        black_periods = []
        with pytest.raises(ValueError):
            fbs.filter_black_periods(black_periods, num_cuts=1)

    def test_cut_all_periods_with_filtered_periods(self, clear_files_teardown):
        """
        Test cut_all_periods method with filtered black periods
        """
        fbs = ffbs(TEST_FILE)
        black_periods = fbs.detect_black_periods()

        # Cut with single filtered period
        filtered_periods = fbs.filter_black_periods(black_periods, num_cuts=1)
        # new black periods -> [{'start': 10.0, 'end': 15.0, 'duration': 5.0}]
        # new content periods -> [{'start': 0.0, 'end': 10.0}, {'start': 15.0, 'end': None}]
        fbs.cut_all_periods(
            os.path.dirname(__file__),
            no_copy=True,
            filtered_black_periods=filtered_periods,
        )

        expected_files = [
            "test_0.0-10.0.mkv",
            "test_15.0-.mkv",
        ]

        for output_file in expected_files:
            assert os.path.exists(os.path.join(os.path.dirname(__file__), output_file))

        # Clean up
        for f in expected_files:
            os.remove(os.path.join(os.path.dirname(__file__), f))
