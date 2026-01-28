"""Rich progress bars and formatting utilities."""

from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from translate_intl.models.translation import MissingKeysReport

console = Console()


@contextmanager
def create_translation_progress():
    """
    Create Rich progress bar for translation operations.

    Yields:
        Progress object with columns for translation tracking

    Example:
        with create_translation_progress() as progress:
            task = progress.add_task("Translating...", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    with progress:
        yield progress


def print_translation_summary(
    lang: str, translated_count: int, total_count: int, elapsed_time: float
) -> None:
    """
    Print translation summary.

    Args:
        lang: Target language code
        translated_count: Number of keys translated
        total_count: Total number of keys
        elapsed_time: Time elapsed in seconds
    """
    speed = translated_count / elapsed_time if elapsed_time > 0 else 0

    console.print(
        f"[green]✓[/green] Language [bold]{lang}[/bold]: "
        f"{translated_count}/{total_count} keys translated "
        f"in {elapsed_time:.1f}s ({speed:.1f} keys/sec)"
    )


def print_missing_keys_table(reports: list[MissingKeysReport]) -> None:
    """
    Print table of missing keys for multiple languages.

    Args:
        reports: List of MissingKeysReport objects
    """
    table = Table(title="Translation Completeness Report")

    table.add_column("Language", style="cyan", no_wrap=True)
    table.add_column("Missing", justify="right", style="red")
    table.add_column("Total", justify="right")
    table.add_column("Complete", justify="right")

    for report in reports:
        missing_count = len(report.missing_keys)
        completion_pct = report.completion_percentage

        # Color code based on completion
        if completion_pct == 100.0:
            completion_style = "green"
        elif completion_pct >= 80.0:
            completion_style = "yellow"
        else:
            completion_style = "red"

        table.add_row(
            report.target_lang,
            str(missing_count),
            str(report.total_keys),
            f"[{completion_style}]{completion_pct:.1f}%[/{completion_style}]",
        )

    console.print(table)


def print_device_info(device_info: dict) -> None:
    """
    Print GPU/CPU device information.

    Args:
        device_info: Dictionary from TranslateGemmaEngine.get_device_info()
    """
    if device_info["cuda_available"]:
        console.print(
            f"[blue]Device:[/blue] {device_info['device']} "
            f"(GPU acceleration enabled, layers: {device_info.get('n_gpu_layers', 'all')})"
        )
    else:
        console.print(f"[blue]Device:[/blue] {device_info['device']} (CPU mode)")
