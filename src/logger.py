import logging
from rich.console import Console
from rich.logging import RichHandler
from config import config

console = Console()

def get_logger(name: str) -> logging.Logger:
    handlers = [RichHandler(console=console, rich_tracebacks=True, show_path=False, markup=True)]
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO), handlers=handlers, format="%(message)s", datefmt="[%H:%M:%S]")
    return logging.getLogger(name)

def print_banner():
    console.print("""
[bold red]
   █████╗ ███╗   ██╗ ██████╗██╗  ██╗ ██████╗ ██████╗
  ██╔══██╗████╗  ██║██╔════╝██║  ██║██╔═══██╗██╔══██╗
  ███████║██╔██╗ ██║██║     ███████║██║   ██║██████╔╝
  ██╔══██║██║╚██╗██║██║     ██╔══██║██║   ██║██╔══██╗
  ██║  ██║██║ ╚████║╚██████╗██║  ██║╚██████╔╝██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/bold red]
[bold white]  Scaffold  •  Anchor/Rust Code Generator  •  Built by LixerDev[/bold white]
[dim]  v1.0.0 | 8 Templates | GPT-4 Generation | TypeScript Tests[/dim]
""")
