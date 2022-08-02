# ffmpeg Black Split

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-black-split.svg)](https://pypi.org/project/ffmpeg-black-split)

Split a video based on black frames.

This tool uses the [`blackdetect` filter](http://ffmpeg.org/ffmpeg-filters.html#blackdetect) from ffmpeg to determine the periods of black content.

Author: Werner Robitza <werner.robitza@gmail.com>

# Requirements

- Python 3.5 or higher
- FFmpeg:
    - download a static build from [their website](http://ffmpeg.org/download.html))
    - put the `ffmpeg` executable in your `$PATH`

# Installation

    pip3 install --user ffmpeg_black_split

Or clone this repository, then run the tool with `python3 -m ffmpeg_black_split`.

# Usage

Run:

    ffmpeg-black-split <input-file>

This might take a while depending on the length of your input file. It'll then split the video into parts, prefixed by the original filename. The audio and video streams will be copied as-is.

The output will be placed in the current directory, with each file being named `<input>_<start>-<end>.mkv`.

# Extended Usage

See `ffmpeg-black-split -h` for more.

# License

ffmpeg_black_split, Copyright (c) 2022 Werner Robitza

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
