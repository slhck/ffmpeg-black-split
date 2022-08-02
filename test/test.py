#!/usr/bin/env pytest

import os
import json
import subprocess
import pytest

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
        stdout, stderr = run_command(
            [
                "python3",
                "-m",
                "ffmpeg_black_split",
                TEST_FILE,
                "-v",
                "-o",
                os.path.dirname(__file__),
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
                {"start": 10.0, "end": 20.0},
                {"start": 20.0},
            ],
        }

        for output_file in [
            "test_10.0-20.0.mkv",
            "test_20.0-.mkv",
            "test_5.0-10.0.mkv",
        ]:
            assert os.path.exists(os.path.join(os.path.dirname(__file__), output_file))
