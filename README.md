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

    Install Playwright's dependencies (Chrome, Firefox, Webkit, and FFmpeg):

    ```bash
    pdm run playwright install
    pdm run playwright install-deps
    ```

4. Install the pre-commit hooks:

    ```bash
    pdm run pre-commit install
    ```

## Getting Started

- Scrape a specific statute from [retsinformation.dk](https://www.retsinformation.dk/):

  ```bash
  pdm run scrape-statute \
    --url https://www.retsinformation.dk/eli/lta/2023/1180 \
    --output-path data/eli-lta-2023-1180.html \
    --force
  ```
