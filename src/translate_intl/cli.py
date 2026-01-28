"""CLI interface for translate-intl."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from translate_intl.core.config import TranslatorConfig
from translate_intl.services.translation_service import TranslationService
from translate_intl.utils.progress import print_missing_keys_table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="translate-intl")
def cli():
    """TranslateGemma CLI for translating next-intl projects."""
    pass


@cli.command()
@click.argument("messages_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--source",
    "-s",
    default="en",
    help="Source language code (default: en)",
    show_default=True,
)
@click.option(
    "--target",
    "-t",
    multiple=True,
    help="Target language codes (can be specified multiple times)",
)
@click.option(
    "--all-languages",
    "-a",
    is_flag=True,
    help="Translate to all discovered languages (excluding source)",
)
@click.option(
    "--max-tokens",
    default=200,
    help="Maximum tokens per generation",
    show_default=True,
)
@click.option(
    "--batch-size",
    default=20,
    help="Number of texts to translate in one batch",
    show_default=True,
)
@click.option(
    "--flat",
    "structure",
    flag_value="flat",
    help="Use flat JSON structure (no key splitting)",
)
@click.option(
    "--nested",
    "structure",
    flag_value="nested",
    help="Use nested JSON structure (split keys by dots)",
)
@click.option(
    "--glossary-path",
    "-g",
    type=click.Path(exists=True, path_type=Path),
    help="Path to glossary JSON file",
)
def translate_all(
    messages_dir: Path,
    source: str,
    target: tuple[str, ...],
    all_languages: bool,
    max_tokens: int,
    batch_size: int,
    structure: str | None = None,
    glossary_path: Path | None = None,
):
    """Translate all keys to target languages."""
    try:
        service = TranslationService(messages_dir)
        nested_flag = None
        if structure == "flat":
            nested_flag = False
        elif structure == "nested":
            nested_flag = True

        # Determine target languages
        if all_languages:
            target_langs = service.file_service.discover_languages(exclude=[source])
            if not target_langs:
                console.print(
                    "[red]Error: No target languages found. "
                    f"Only {source}.json exists in {messages_dir}[/red]"
                )
                return
            console.print(f"[blue]Auto-discovered languages:[/blue] {', '.join(target_langs)}")
        elif target:
            target_langs = list(target)
        else:
            console.print(
                "[red]Error: Please specify target languages with --target "
                "or use --all-languages[/red]"
            )
            return

        service.translate_all(
            source_lang=source,
            target_langs=target_langs,
            max_tokens=max_tokens,
            batch_size=batch_size,
            nested=nested_flag,
            glossary_path=glossary_path,
        )

        console.print("\n[green bold]✓ Translation completed![/green bold]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.argument("messages_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--source",
    "-s",
    default="en",
    help="Source language code (default: en)",
    show_default=True,
)
@click.option(
    "--target",
    "-t",
    multiple=True,
    help="Target language codes (can be specified multiple times)",
)
@click.option(
    "--all-languages",
    "-a",
    is_flag=True,
    help="Translate to all discovered languages (excluding source)",
)
@click.option(
    "--max-tokens",
    default=200,
    help="Maximum tokens per generation",
    show_default=True,
)
@click.option(
    "--batch-size",
    default=20,
    help="Number of texts to translate in one batch",
    show_default=True,
)
@click.option(
    "--flat",
    "structure",
    flag_value="flat",
    help="Use flat JSON structure (no key splitting)",
)
@click.option(
    "--nested",
    "structure",
    flag_value="nested",
    help="Use nested JSON structure (split keys by dots)",
)
@click.option(
    "--glossary-path",
    "-g",
    type=click.Path(exists=True, path_type=Path),
    help="Path to glossary JSON file",
)
def translate_missing(
    messages_dir: Path,
    source: str,
    target: tuple[str, ...],
    all_languages: bool,
    max_tokens: int,
    batch_size: int,
    structure: str | None = None,
    glossary_path: Path | None = None,
):
    """Translate only missing keys to target languages."""
    try:
        service = TranslationService(messages_dir)
        nested_flag = None
        if structure == "flat":
            nested_flag = False
        elif structure == "nested":
            nested_flag = True

        # Determine target languages
        if all_languages:
            target_langs = service.file_service.discover_languages(exclude=[source])
            if not target_langs:
                console.print(
                    "[red]Error: No target languages found. "
                    f"Only {source}.json exists in {messages_dir}[/red]"
                )
                return
            console.print(f"[blue]Auto-discovered languages:[/blue] {', '.join(target_langs)}")
        elif target:
            target_langs = list(target)
        else:
            console.print(
                "[red]Error: Please specify target languages with --target "
                "or use --all-languages[/red]"
            )
            return

        service.translate_missing(
            source_lang=source,
            target_langs=target_langs,
            max_tokens=max_tokens,
            batch_size=batch_size,
            nested=nested_flag,
            glossary_path=glossary_path,
        )

        console.print("\n[green bold]✓ Translation completed![/green bold]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.argument("messages_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--source",
    "-s",
    default="en",
    help="Source language code (default: en)",
    show_default=True,
)
@click.option(
    "--target",
    "-t",
    multiple=True,
    help="Target language codes (can be specified multiple times)",
)
@click.option(
    "--all-languages",
    "-a",
    is_flag=True,
    help="Check all discovered languages (excluding source)",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
    show_default=True,
)
@click.option(
    "--flat",
    "structure",
    flag_value="flat",
    help="Use flat JSON structure",
)
@click.option(
    "--nested",
    "structure",
    flag_value="nested",
    help="Use nested JSON structure",
)
def check(
    messages_dir: Path,
    source: str,
    target: tuple[str, ...],
    all_languages: bool,
    output_format: str,
    structure: str | None = None,
):
    """Check translation completeness."""
    try:
        service = TranslationService(messages_dir)
        nested_flag = None
        if structure == "flat":
            nested_flag = False
        elif structure == "nested":
            nested_flag = True

        # Determine target languages
        if all_languages:
            target_langs = service.file_service.discover_languages(exclude=[source])
            if not target_langs:
                console.print(
                    "[red]Error: No target languages found. "
                    f"Only {source}.json exists in {messages_dir}[/red]"
                )
                return
        elif target:
            target_langs = list(target)
        else:
            console.print(
                "[red]Error: Please specify target languages with --target "
                "or use --all-languages[/red]"
            )
            return

        reports = service.check_completeness(
            source_lang=source, target_langs=target_langs, nested=nested_flag
        )

        if output_format == "table":
            print_missing_keys_table(reports)
        elif output_format == "json":
            json_data = [
                {
                    "language": r.target_lang,
                    "missing_keys": r.missing_keys,
                    "total_keys": r.total_keys,
                    "completion_percentage": round(r.completion_percentage, 2),
                }
                for r in reports
            ]
            console.print(json.dumps(json_data, indent=2, ensure_ascii=False))
        elif output_format == "markdown":
            console.print("| Language | Missing | Total | Complete |")
            console.print("|----------|---------|-------|----------|")
            for r in reports:
                console.print(
                    f"| {r.target_lang} | {len(r.missing_keys)} | "
                    f"{r.total_keys} | {r.completion_percentage:.1f}% |"
                )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
def languages():
    """Show supported languages."""
    from translate_intl.core.languages import LANGUAGE_MAP

    table = Table(title="TranslateGemma Supported Languages (55+)")
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Language", style="green")

    for code, name in sorted(LANGUAGE_MAP.items()):
        table.add_row(code, name)

    console.print(table)
    console.print(
        "\n[dim]Note: Regional variants (e.g., en-US, pt-BR) are also supported[/dim]"
    )


if __name__ == "__main__":
    cli()
