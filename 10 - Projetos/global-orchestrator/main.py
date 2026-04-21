import typer
from rich.console import Console
from rich.panel import Panel

from core.debug.config import build_runtime_tracer
from core.orchestrator import GlobalOrchestrator

app = typer.Typer(help="Global Agent Orchestrator CLI")
console = Console()


def _build_orchestrator(
    *,
    debug: bool,
    trace: bool,
    jsonl: str | None,
) -> GlobalOrchestrator:
    tracer = build_runtime_tracer(debug=debug, trace=trace, jsonl_path=jsonl)
    return GlobalOrchestrator(tracer=tracer)


@app.command()
def chat(
    debug: bool = typer.Option(False, "--debug", help="Enable debug events (INFO+)."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace events (DEBUG+ with payloads)."),
    jsonl: str | None = typer.Option(None, "--jsonl", help="Optional JSONL file path for event logs."),
):
    """Inicia uma sessão de chat interativa com o Orquestrador."""
    orchestrator = _build_orchestrator(debug=debug, trace=trace, jsonl=jsonl)
    console.print(Panel.fit("🚀 [bold cyan]Global Orchestrator Ativo[/bold cyan]\nDigite 'sair' para encerrar.", border_style="blue"))
    
    while True:
        user_input = console.input("[bold green]Você:[/bold green] ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
            
        with console.status("[bold yellow]Pensando e Orquestrando...[/bold yellow]"):
            response = orchestrator.process_request(user_input)
            
        if response["status"] == "success":
            console.print(f"[bold blue]Orquestrador (Skill: {response['skill']}):[/bold blue]")
            console.print(Panel(str(response["result"]), border_style="green"))
        else:
            console.print(f"[bold blue]Orquestrador:[/bold blue] {response['content']}")


@app.command()
def list_skills(
    debug: bool = typer.Option(False, "--debug", help="Enable debug events (INFO+)."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace events (DEBUG+ with payloads)."),
    jsonl: str | None = typer.Option(None, "--jsonl", help="Optional JSONL file path for event logs."),
):
    """Lista todas as habilidades descobertas no sistema."""
    orchestrator = _build_orchestrator(debug=debug, trace=trace, jsonl=jsonl)
    console.print("[bold cyan]Habilidades Instaladas:[/bold cyan]")
    for skill_name, skill in orchestrator.skills.items():
        console.print(f"- [bold green]{skill_name}[/bold green]: {skill.description}")


@app.command()
def ask(
    message: str,
    debug: bool = typer.Option(False, "--debug", help="Enable debug events (INFO+)."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace events (DEBUG+ with payloads)."),
    jsonl: str | None = typer.Option(None, "--jsonl", help="Optional JSONL file path for event logs."),
):
    """Executa uma pergunta unica sem abrir o chat interativo."""
    orchestrator = _build_orchestrator(debug=debug, trace=trace, jsonl=jsonl)
    with console.status("[bold yellow]Pensando e Orquestrando...[/bold yellow]"):
        response = orchestrator.process_request(message)

    if response["status"] == "success":
        console.print(f"[bold blue]Orquestrador (Skill: {response['skill']}):[/bold blue]")
        console.print(Panel(str(response["result"]), border_style="green"))
    else:
        console.print(f"[bold blue]Orquestrador:[/bold blue] {response['content']}")


if __name__ == "__main__":
    app()
