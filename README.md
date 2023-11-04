# Paraglide

An app for searching through Danish statutes.

## Development Setup

1. Ensure [pyenv](https://github.com/pyenv/pyenv) and [PDM](https://pdm.fming.dev/) are installed.

2. Install the correct Python version:

    ```bash
    pyenv install
    ```

3. Install the dependencies:

    ```bash
    pdm use python
    pdm install
    ```

4. Install the pre-commit hooks:

    ```bash
    pdm run pre-commit install
    ```
