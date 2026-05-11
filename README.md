# biz.dfch.IncoseIso25010Refiner

## Installation

1. Make a local copy of the repository

    `git clone https://github.com/dfensgmbh/biz.dfch.IncoseIso25010Refiner.git`
1. Create environment and install dependencies

    `uv sync --python 3.13 --extra dev --extra build`

## Start the programme
1. Add API key to local terminal session

    `$ENV:CHAT_API_TOKEN="..."`
1. Change to `src` directory

    `cd src`
1. When there is no Python environment active, activate the Python environment

    Windows: `.\.venv\Scripts\Activate.ps1`
    Linux: `source ./.venv\bin/activate`
1. Start the programme

    `python -m biz query -t ./prompt1.md -p "The user interface must be intuitive to use."`
