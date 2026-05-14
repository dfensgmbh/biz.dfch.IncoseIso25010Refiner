# biz.dfch.IncoseIso25010Refiner

## Installation

1. Make a local copy of the repository

    `git clone https://github.com/dfensgmbh/biz.dfch.IncoseIso25010Refiner.git`

1. Create environment and install dependencies

    `uv sync --python 3.13 --extra dev --extra build`

If `uv` is not available you can install it with these commands:

Windows: `winget install --id=astral-sh.uv -e`
Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `wget -qO- https://astral.sh/uv/install.sh | sh`

Note: on Windows if `uv` is not in the `PATH` you can find it in the `~\AppData\roaming\Python...\Scripts\...` directory.

## Start the programme

1. Add API key to local terminal session

    Windows (PowerShell): `$ENV:CHAT_API_TOKEN="..."`

    Windows (Command Prompt): `set CHAT_API_TOKEN=...`

    Linux: `export CHAT_API_TOKEN="..."

1. Change to `src` directory

    `cd src`

1. When there is no Python environment active, activate the Python environment

    Windows: `.\.venv\Scripts\Activate.ps1`

    Linux: `source ./.venv\bin/activate`

1. Start the programme with prompt text

    `python -m biz query -t ./prompt1.md -p "The user interface must be intuitive to use."`

    Here, `-p` contains the *prompt text*. When you also specify `-t` (as in the example above), *prompt text* adds to the text from the specified template.

    Note: `-p` and `-i` are mutually exclusive.
 
1. Start the programme with prompt file

    `python -m biz query -t ./prompt1.md -i ~/some-text-file-with-prompt.txt`

    Here, `-i` contains the path to a file with *prompt text*. When you also specify `-t` (as in the example above), *prompt text* adds to the text from the specified template.

    Note: `-p` and `-i` are mutually exclusive.
