# Sultek Connector

## TODO:s

- implement retry with backoff

## Usage

Install uv

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install Python and create a venv

```shell
uv python install 3.12
uv sync
```

Runs unit tests

```shell
uv run pytest tests/
```

Start the mock server

```shell
uv run python tools/http_server.py
```
In a new terminal, run the example code that outputs JSON

```shell
uv run python example.py
```