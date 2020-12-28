# sq100

![CI](https://github.com/nachstedt/sq100/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/nachstedt/sq100/branch/develop/graph/badge.svg?token=71XLJQL5CQ)](https://codecov.io/gh/nachstedt/sq100)

A replacement for the annoying original Software of the SQ100 pulse clock.
This project is a complete rewrite of the gh615 project:
https://code.google.com/archive/p/gh615/

## Installation

As of now, the application can only be obtained directly from the git repository:

```bash
git clone https://github.com/tnachstedt/sq100
python3 sq100/setup.py install --user
```

## Usage

There are two distinct usage modes. On the one hand, you can use command line
arguments to control the application:

```bash
sq100 list
sq100 download 1,4
```

On the other hand, you can enter the interactive shell:

```bash
sq100
(sq100) list
(sq100) download 1,4
```

### Available Commands:

| Command  | Arguments | Description                                       |
| -------- | --------- | ------------------------------------------------- |
| list     |           | Show list of available tracks on the deivce       |
| download | track_ids | Download the tracks with the specified ids to gpx |

## License

This project is licensed under the terms of the
[GNU General Public License v3.0](http://www.gnu.org/licenses/gpl-3.0.txt)
