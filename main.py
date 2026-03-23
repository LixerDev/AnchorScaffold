#!/usr/bin/env python3
"""
AnchorScaffold — Anchor/Rust Program Generator
Built by LixerDev
"""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich import box

from config import config
from src.logger import get_logger, print_banner
from src.models import TemplateKind, TEMPLATE_REGISTRY, GenerationRequest
from src.parser import parse_description, slugify, extract_program_name
from src.generator import Generator
from src.scaffolder import scaffold_project

app = typer.Typer(
    help="AnchorScaffold — Generate complete Anchor/Rust programs from natural language",
    no_args_is_help=True
)
console = Console()
logger = get_logger(__name__)


@app.command()
def generate(
    description: str = typer.Argument(..., help='Natural language description (e.g. "staking program with time-based rewards")'),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Program name (auto-detected if not set)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI enhancement (template-only)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without writing files"),
):
    """
    Generate an Anchor program from a natural language description.

    AnchorScaffold will:
    1. Analyze your description to find the best matching template
    2. Use GPT-4 to customize/enhance the code (if OPENAI_API_KEY is set)
    3. Generate a complete project with Anchor.toml, Cargo.toml, lib.rs, and TypeScript tests
    """
    print_banner()

    # Determine program name
    program_name = name
    if not program_name:
        extracted = extract_program_name(description)
        if extracted:
            program_name = slugify(extracted)
            console.print(f"[dim]Program name extracted from description: {program_name}[/dim]")
        else:
            program_name = "my-anchor-program"

    # Parse description to find best template
    template_kind, score = parse_description(description)

    console.print(f"\n[bold]📋 Generation Plan[/bold]")
    console.print(f"  Description:  [dim]{description[:80]}...[/dim]" if len(description) > 80 else f"  Description:  [dim]{description}[/dim]")
    console.print(f"  Program name: [bold cyan]{program_name}[/bold cyan]")
    console.print(f"  Template:     [bold green]{template_kind.value}[/bold green]", end="")
    if score > 0:
        console.print(f" [dim](confidence: {score:.0f})[/dim]")
    else:
        console.print(" [dim](custom — AI generation)[/dim]")

    if config.ai_enabled and not no_ai:
        console.print(f"  AI Mode:      [bold green]✅ GPT-4 enabled[/bold green]")
    else:
        console.print(f"  AI Mode:      [dim]Template-only[/dim]")

    if dry_run:
        console.print("\n[yellow]Dry run — no files will be written.[/yellow]")
        _show_would_create(program_name, output)
        return

    request = GenerationRequest(
        description=description,
        program_name=program_name,
        template_kind=template_kind,
        output_dir=output or config.OUTPUT_DIR,
        use_ai=not no_ai,
    )

    async def _run():
        generator = Generator()
        console.print("\n[dim]Generating program...[/dim]")
        program = await generator.generate(request)
        project_path = scaffold_project(program, output or config.OUTPUT_DIR)
        _show_success(program_name, project_path, program.ai_generated, template_kind)

    asyncio.run(_run())


@app.command("new")
def new_from_template(
    template: str = typer.Argument(..., help="Template name: staking, escrow, vesting, dao, lottery, multisig, marketplace, launchpad"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Program name"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """
    Generate a program from a specific template directly (no AI needed).

    Example:
      anchor-scaffold new staking --name my-staking
      anchor-scaffold new dao --name governance --output ./projects
    """
    print_banner()

    try:
        kind = TemplateKind(template.lower())
    except ValueError:
        valid = ", ".join(t.value for t in TemplateKind if t != TemplateKind.CUSTOM)
        console.print(f"[red]Unknown template: {template}[/red]")
        console.print(f"[dim]Valid options: {valid}[/dim]")
        raise typer.Exit(1)

    program_name = name or f"my-{kind.value}-program"

    request = GenerationRequest(
        description="",
        program_name=program_name,
        template_kind=kind,
        output_dir=output or config.OUTPUT_DIR,
        use_ai=False,  # Template mode — no AI needed
    )

    async def _run():
        generator = Generator()
        console.print(f"\n[dim]Scaffolding [bold]{kind.value}[/bold] template as [bold]{program_name}[/bold]...[/dim]")
        program = await generator.generate(request)
        project_path = scaffold_project(program, output or config.OUTPUT_DIR)
        _show_success(program_name, project_path, False, kind)

    asyncio.run(_run())


@app.command("templates")
def list_templates(verbose: bool = typer.Option(False, "--verbose", "-v")):
    """List all available built-in templates with their instructions and accounts."""
    print_banner()

    table = Table(box=box.ROUNDED, show_header=True, title="Built-in Anchor Templates")
    table.add_column("Template", style="bold", width=14)
    table.add_column("Description", width=42)
    table.add_column("Instructions", width=38)
    table.add_column("Complexity", width=10)

    for kind, info in TEMPLATE_REGISTRY.items():
        if kind == TemplateKind.CUSTOM:
            continue
        table.add_row(
            f"[green]{kind.value}[/green]",
            info.description[:40] + "...",
            ", ".join(info.instructions),
            f"[{'yellow' if info.complexity == 'Medium' else 'red' if info.complexity == 'Advanced' else 'green'}]{info.complexity}[/]",
        )

    console.print(table)
    console.print(f"\n[dim]Usage: python main.py new <template> --name <program-name>[/dim]")
    console.print(f"[dim]       python main.py generate \"<natural language description>\"[/dim]\n")


@app.command("explain")
def explain_template(
    template: str = typer.Argument(..., help="Template to explain"),
):
    """Show detailed information about a specific template."""
    print_banner()

    try:
        kind = TemplateKind(template.lower())
    except ValueError:
        console.print(f"[red]Unknown template: {template}[/red]")
        raise typer.Exit(1)

    info = TEMPLATE_REGISTRY.get(kind)
    if not info:
        console.print(f"[red]No info for template: {template}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]🦀 {info.display_name}[/bold]\n")
    console.print(f"[dim]{info.description}[/dim]\n")

    console.print(f"[bold]Instructions:[/bold]")
    for ix in info.instructions:
        console.print(f"  • {ix}")

    console.print(f"\n[bold]Accounts:[/bold]")
    for acc in info.accounts:
        console.print(f"  • {acc}")

    console.print(f"\n[bold]Error Codes:[/bold]")
    for err in info.errors:
        console.print(f"  • [red]{err}[/red]")

    console.print(f"\n[bold]Events:[/bold]")
    for evt in info.events:
        console.print(f"  • [cyan]{evt}[/cyan]")

    console.print(f"\n[bold]Complexity:[/bold] {info.complexity}")
    console.print(f"[bold]Keywords:[/bold] {', '.join(info.keywords)}\n")


def _show_success(name: str, path: str, ai_used: bool, kind: TemplateKind):
    console.print(f"\n[bold green]✅ Program generated successfully![/bold green]\n")
    console.print(f"  [bold]Name:[/bold]     {name}")
    console.print(f"  [bold]Template:[/bold] {kind.value}")
    console.print(f"  [bold]AI Used:[/bold]  {'✅ GPT-4' if ai_used else 'No (template)'}")
    console.print(f"  [bold]Path:[/bold]     {path}\n")
    console.print(f"  [bold]Files created:[/bold]")
    console.print(f"    📄 programs/{name}/src/lib.rs    ← Main Anchor program")
    console.print(f"    📄 tests/{name}.ts              ← TypeScript tests")
    console.print(f"    📄 Anchor.toml                   ← Workspace config")
    console.print(f"    📄 Cargo.toml                    ← Rust workspace")
    console.print(f"    📄 app/index.ts                  ← Client SDK stub\n")
    console.print(f"  [bold]Next steps:[/bold]")
    console.print(f"    [cyan]cd {path}[/cyan]")
    console.print(f"    [cyan]anchor build[/cyan]")
    console.print(f"    [cyan]anchor test[/cyan]\n")


def _show_would_create(name: str, output: Optional[str]):
    base = Path(output or config.OUTPUT_DIR) / name
    files = [
        f"{base}/Anchor.toml",
        f"{base}/Cargo.toml",
        f"{base}/programs/{name}/Cargo.toml",
        f"{base}/programs/{name}/src/lib.rs",
        f"{base}/tests/{name}.ts",
        f"{base}/migrations/deploy.ts",
        f"{base}/app/index.ts",
    ]
    console.print("\n[bold]Would create:[/bold]")
    for f in files:
        console.print(f"  {f}")


if __name__ == "__main__":
    app()
