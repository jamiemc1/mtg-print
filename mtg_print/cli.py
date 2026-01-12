from pathlib import Path
from typing import Annotated

import typer

from mtg_print.cache import ImageCache
from mtg_print.decklist import parse_decklist
from mtg_print.scryfall import CardNotFoundError, ScryfallClient
from mtg_print.sheet import SheetGenerator
from mtg_print.terminal import display_image

app = typer.Typer(help="MTG proxy printing tool", no_args_is_help=True)


@app.command()
def build(
    decklist_path: Annotated[Path, typer.Argument(help="Path to decklist file")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output PDF path")] = None,
    set_override: Annotated[
        list[str], typer.Option("--set", "-s", help="Override set for card: 'Card Name=SET'")
    ] = [],
) -> None:
    """Build printable PDF from decklist."""
    overrides = {}
    for override in set_override:
        if "=" in override:
            name, set_code = override.rsplit("=", 1)
            overrides[name.strip()] = set_code.strip()

    decklist = parse_decklist(decklist_path)
    typer.echo(f"Parsed {len(decklist.entries)} unique cards ({decklist.total_cards} total)")

    client = ScryfallClient()
    cache = ImageCache()
    images: list[Path] = []

    with typer.progressbar(decklist.entries, label="Fetching cards") as entries:
        for entry in entries:
            set_code = overrides.get(entry.name, entry.set_override)
            try:
                printing = client.get_card_by_name(entry.name, set_code)
            except CardNotFoundError:
                typer.echo(f"\nCard not found: '{entry.name}'", err=True)
                raise typer.Exit(1)

            for _ in range(entry.count):
                front = cache.get_or_download(printing, client, face_index=0)
                images.append(front)
                if printing.is_double_faced:
                    back = cache.get_or_download(printing, client, face_index=1)
                    images.append(back)

    output_path = output or decklist_path.with_suffix(".pdf")
    generator = SheetGenerator()
    generator.generate(images, output_path)
    typer.echo(f"Generated {output_path} with {len(images)} card images")


@app.command()
def search(
    card_name: Annotated[str, typer.Argument(help="Card name to search")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 10,
    preview: Annotated[bool, typer.Option("--preview", "-p", help="Show card thumbnails")] = False,
) -> None:
    """Search for card printings (oldest first)."""
    client = ScryfallClient()
    try:
        printings = client.search_printings(card_name)
    except CardNotFoundError:
        typer.echo(f"No card found matching '{card_name}'", err=True)
        raise typer.Exit(1)

    for i, p in enumerate(printings[:limit], 1):
        dfc = " (DFC)" if p.is_double_faced else ""
        typer.echo(f"  {i}. {p.set_code.upper()} ({p.release_date}) - {p.set_name}{dfc}")

        if preview and p.faces and p.faces[0].image_uri_small:
            response = client.client.get(p.faces[0].image_uri_small)
            if response.status_code == 200:
                display_image(response.content, width=15)


@app.command()
def cache(
    clear: Annotated[bool, typer.Option("--clear", help="Clear image cache")] = False,
    stats: Annotated[bool, typer.Option("--stats", help="Show cache statistics")] = False,
) -> None:
    """Manage image cache."""
    image_cache = ImageCache()

    if clear:
        count = image_cache.clear()
        typer.echo(f"Cleared {count} cached images")
    elif stats:
        s = image_cache.stats()
        size_mb = s["total_size_bytes"] / (1024 * 1024)
        typer.echo(f"Cached images: {s['file_count']}")
        typer.echo(f"Total size: {size_mb:.2f} MB")
    else:
        typer.echo("Use --clear or --stats")


if __name__ == "__main__":
    app()
