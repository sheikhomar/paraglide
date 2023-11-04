from pathlib import Path

import click
from paraglide.parsers.retsinformation import RetsinformationStatuteParser


@click.command()
@click.option("-i", "--input-path", default="data/eli-lta-2023-1180.html")
@click.option("-o", "--output-path", default="data/eli-lta-2023-1180.json")
@click.option(
    "-f", "--force", is_flag=True, help="Overwrite output file if it already exists"
)
def main(input_path: str, output_path: str, force: bool) -> None:
    input_path_ = Path(input_path)
    if not input_path_.exists():
        raise click.BadParameter(f"File {input_path_} does not exist")

    output_path_ = Path(output_path)
    if force is False and output_path_.exists():
        raise click.BadParameter(
            f"File {output_path_} already exists. Use --force to overwrite it."
        )

    print(f"Parsing {input_path_} ...")
    parser = RetsinformationStatuteParser(
        file_path=input_path_,
    )
    statute = parser.run()
    print(
        f"File parsed successfully. Found {len(statute.chapters)} chapters in the statute."
    )
    print(f"Writing output to {output_path} ...")
    with open(output_path_, "w") as f:
        f.write(statute.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
