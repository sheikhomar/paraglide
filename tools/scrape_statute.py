from pathlib import Path
from typing import Optional

import click
from playwright.async_api import async_playwright
from anyio import run as anyio_run
from urllib.parse import urlparse


async def get_page_content(url: str, css_to_wait_for: Optional[str] = None) -> str:
    """Get the content of a page.

    Args:
        url: The URL of the page.
        css_to_wait_for: A CSS selector to wait for before returning the content.

    Returns:
        The content of the page.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
        if css_to_wait_for and len(css_to_wait_for.strip()) > 0:
            await page.wait_for_selector(css_to_wait_for)
        content = await page.content()
        await browser.close()
        return content


def generate_file_path(url: str) -> Path:
    """Generate a file path from a URL.

    Args:
        url: The URL to generate a file path from.

    Returns:
        A file path.
    """
    parsed_url = urlparse(url)
    path_parts = [part for part in parsed_url.path.split("/") if len(part.strip()) > 0]
    file_name = "-".join(path_parts)
    return Path(f"data/{file_name}.html")


async def runner(url: str, output_path: Path) -> None:
    print(f"Getting content from {url}...")
    content = await get_page_content(url=url, css_to_wait_for="p.Fodnote")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing content to {output_path}...")
    with open(output_path, "w") as f:
        f.write(content)


@click.command()
@click.option("-u", "--url", required=True, help="The URL of the page to scrape")
@click.option(
    "-o",
    "--output-path",
    required=False,
    help="The path of the output file. Leave blank to generate a path from the URL.",
)
@click.option(
    "-f", "--force", is_flag=True, help="Overwrite output file if it already exists"
)
def main(url: str, output_path: str, force: bool):
    if output_path is None or len(output_path.strip()) == 0:
        output_path = generate_file_path(url=url)
    else:
        output_path = Path(output_path)

    if force is False and output_path.exists():
        raise click.BadParameter(
            f"File {output_path} already exists. Use --force to overwrite it."
        )

    anyio_run(runner, url, output_path)


if __name__ == "__main__":
    main()
