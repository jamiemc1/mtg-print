# mtg-print

CLI tool for printing Magic: The Gathering proxy sheets. Parses decklists, fetches card images from Scryfall, and generates printable PDFs.

![Demo](docs/demo.gif)

## Installation

```bash
pipx install mtg-print
```

Or run directly:

```bash
uvx mtg-print --help
```

## Quick start

```bash
mtg-print build docs/example.txt --interactive
```

## Usage

### Build a PDF from a decklist

```bash
mtg-print build deck.txt
mtg-print build deck.txt -o output.pdf
```

Basic lands are automatically filtered. Cards default to their oldest printing.

### Interactive art selection

```bash
mtg-print build deck.txt --interactive
```

Displays available printings with thumbnails and lets you choose. Selections are saved for future builds.

### Override specific card art

```bash
mtg-print build deck.txt -s "Swords to Plowshares=ICE"
```

### Search card printings

```bash
mtg-print search "Sylvan Library"
mtg-print search "Elvish Reclaimer" --preview
```

### Manage preferences

```bash
mtg-print prefs           # View saved art preferences
mtg-print prefs --clear   # Clear all preferences
```

### Manage cache

```bash
mtg-print cache --stats   # Show cache size
mtg-print cache --clear   # Clear cached images
```

## Supported decklist formats

- Moxfield / MTG Arena: `4 Elvish Reclaimer (MH2) 166`
- MTGGoldfish: `4 Elvish Reclaimer <mh2>`
- DeckedBuilder: `4 Elvish Reclaimer`
- Manabox: `1 Card Name (SET) 123 *F*`
- TopDecked: `4 Spyglass Siren`

## Development

```bash
git clone https://github.com/jamiemc1/mtg-print.git
cd mtg-print
uv sync --dev
uv run pytest
uv run pre-commit run --all-files
```

---

Card images © Wizards of the Coast
