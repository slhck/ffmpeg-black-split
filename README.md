# ffmpeg Black Split

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-black-split.svg)](https://pypi.org/project/ffmpeg-black-split)

Split a video based on black frames.

This tool uses the [`blackdetect` filter](http://ffmpeg.org/ffmpeg-filters.html#blackdetect) from ffmpeg to determine the periods of black content.

Author: Werner Robitza <werner.robitza@gmail.com>

Contents:

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [JSON Output](#json-output)
  - [Extended Usage](#extended-usage)
- [License](#license)

## Requirements

- Python 3.7 or higher
- FFmpeg:
    - download a static build from [their website](http://ffmpeg.org/download.html))
    - put the `ffmpeg` executable in your `$PATH`

## Installation

    pip3 install --user ffmpeg_black_split

Or clone this repository, then run the tool with `python3 -m ffmpeg_black_split`.

## Usage

Run:

    ffmpeg-black-split <input-file>

This might take a while depending on the length of your input file. It'll then split the video into parts, prefixed by the original filename. The audio and video streams will be copied as-is.

The output will be placed in the current directory, with each file being named `<input>_<start>-<end>.mkv`.

Note that by default, cutting is not that accurate, as stream-copying is used. If you want to re-encode using x264, you can use the `--no-copy` flag. (Future versions may have better options for encoding.)

Pass the `--no-split` option to disable the actual splitting.

### JSON Output

Example to get just the JSON output:

```bash
ffmpeg-black-split input.mkv -p -v --no-split 2>/dev/null
```

Returns:

```json
{
  "black_periods": [
    {
      "start": 0.0,
      "end": 5.0,
      "duration": 5.0
    },
    {
      "start": 10.0,
      "end": 15.0,
      "duration": 5.0
    },
    {
      "start": 20.0,
      "end": 25.0,
      "duration": 5.0
    }
  ],
  "content_periods": [
    {
      "start": 5.0,
      "end": 10.0
    },
    {
      "start": 10.0,
      "end": 20.0
    },
    {
      "start": 20.0
    }
  ]
}
```

### Extended Usage

See `ffmpeg-black-split -h` for more:

```
usage: __main__.py [-h] [-d BLACK_MIN_DURATION] [-r PICTURE_BLACK_RATIO_TH]
                   [-t PIXEL_BLACK_TH] [-o OUTPUT_DIRECTORY] [--no-split]
                   [--no-copy] [-p] [-v]
                   input

ffmpeg-black-split v0.3.0

positional arguments:
  input                 input file

optional arguments:
  -h, --help            show this help message and exit
  -d BLACK_MIN_DURATION, --black-min-duration BLACK_MIN_DURATION
                        Set the minimum detected black duration expressed in
                        seconds. It must be a non-negative floating point
                        number. (default: 2.0)
  -r PICTURE_BLACK_RATIO_TH, --picture-black-ratio-th PICTURE_BLACK_RATIO_TH
                        Set the threshold for considering a picture 'black'
                        (default: 0.98)
  -t PIXEL_BLACK_TH, --pixel-black-th PIXEL_BLACK_TH
                        Set the threshold for considering a pixel 'black'
                        (default: 0.1)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Set the output directory. Default is the current
                        working directory. (default: None)
  --no-split            Don't split the video into segments. (default: False)
  --no-copy             Don't stream-copy, but re-encode the video. (default:
                        False)
  -p, --progress        Show a progress bar on stderr (default: False)
  -v, --verbose         Print verbose info to stderr, and JSON of black and
                        content periods to stdout (default: False)
```

## License

ffmpeg_black_split, Copyright (c) 2022 Werner Robitza

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
