import typer
from rich.console import Console
from rich.panel import Panel
from core.orchestrator import GlobalOrchestrator

app = typer.Typer(help="Global Agent Orchestrator CLI")
console = Console()
orchestrator = GlobalOrchestrator()

@app.command()
def chat():
    """Inicia uma sessão de chat interativa com o Orquestrador."""
    console.print(Panel.fit("🚀 [bold cyan]Global Orchestrator Ativo[/bold cyan]\nDigite 'sair' para encerrar.", border_style="blue"))
    
    while True:
        user_input = console.input("[bold green]Você:[/bold green] ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
            
        with console.status("[bold yellow]Pensando e Orquestrando...[/bold yellow]"):
            response = orchestrator.process_request(user_input)
            
        if response["status"] == "success":
            console.print(f"[bold blue]Oruestrador (Skill: {response['skill']}):[/bold blue]")
            console.print(Panel(str(response["result"]), border_style="green"))
        else:
            console.print(f"[bold blue]Orquestrador:[/bold blue] {response['content']}")

@app.command()
def list_skills():
    """Lista todas as habilidades descobertas no sistema."""
    console.print("[bold cyan]Habilidades Instaladas:[/bold cyan]")
    for skill_name, skill in orchestrator.skills.items():
        console.print(f"- [bold green]{skill_name}[/bold green]: {skill.description}")

if __name__ == "__main__":
    app()
