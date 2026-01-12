from rich.console import Console
from rich.theme import Theme


ARINFRA_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "prompt": "bold magenta",
        "highlight": "bold blue",
        "muted": "dim white",
    }
)

console = Console(theme=ARINFRA_THEME)
