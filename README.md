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

## Start the programme with `Python`

1. Add API key to local terminal session

    Windows (PowerShell): `$ENV:CHAT_API_TOKEN="..."`

    Windows (Command Prompt): `set CHAT_API_TOKEN=...`

    Linux: `export CHAT_API_TOKEN=...`

1. Change to `src` directory

    `cd src`

1. When there is no Python environment active, activate the Python environment

    Windows: `.\.venv\Scripts\Activate.ps1`

    Linux: `source ./.venv\bin/activate`

    Note: when you use `uv`

1. Start the programme with prompt text

    ```
    python -m biz query -i "The user interface must be intuitive to use."
    ```

1. Start the programme with prompt file

    ```
    python -m biz query -i ~/some-text-file-with-prompt.txt
    ```

## Start the programme with `uv`

With `uv` you can start the programme directly in the root folder of the git repository. `uv` will also make the virtual environment active.

1. Start with `uv` and get help

    ```
    uv run req --help
    ```

    ![Show req help](https://github.com/user-attachments/assets/31009441-eb16-4636-8f24-189ec59c4d89)

1. Start specific command with `uv` and get help for this command

    ```
    uv run req init --help
    uv run req refine --help
    ```

    ![Show req init help](https://github.com/user-attachments/assets/6fd44a5b-a530-46a6-b017-579f887a4251)

## Prepare a workspace (`init`)

Before you begin to refine requirements, you create a workspace. For this you use `req init`. You must specify a `workspace`. This is the base folder for all your requirement sessions. When you often work in the same base folder, you can set an environment variable (`export REQ_WORKSPACE=/data/requirements`). You can also specify a relative path 

```
uv run req init --workspace ../sessions -id ABCD-1234 --input "'Automatic Teller System' (ATM): The user wants to withdraw cash."
```

![Start new session](https://github.com/user-attachments/assets/64549934-681f-4fe0-8bff-2ed6ec4d9767)

## Refine requirements (`refine`)

```
uv run req --help
```

![Show req refine help](https://github.com/user-attachments/assets/ef70f921-5b37-4a33-898e-61f276ce8b50)

```
uv run req refine --workspace ../sessions -id ABCD-1234
```

![Refine requirements](https://github.com/user-attachments/assets/f13b4f46-0646-45db-a95e-becfbbf67b31)


## Restore last source document (`restore`)

```
uv run req restore --help
```

![Show req restore help](https://github.com/user-attachments/assets/a7dad735-399b-47f1-a448-919a94ad822f)

```
uv run req restore --workspace ../sessions -id ABCD-1234

uv run req restore --workspace ../sessions -id ABCD-1234 -y
```

![Restore previous version of source docuemnt](https://github.com/user-attachments/assets/5795f4b2-a9ea-4418-b3cc-3d10c5da07cd)


NOTE: we used [`asciinema`](https://asciinema.org/) to record the terminal sessions and [`agg`](https://docs.asciinema.org/manual/agg/) to make animated GIFs.
