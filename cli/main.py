from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from pathlib import Path
import json
import sys

app = typer.Typer(help="Code-Swarm CLI")
console = Console()


@app.command()
def status():
    console.print(Panel("[bold cyan]Code-Swarm Status[/bold cyan]", expand=False))
    agents_file = Path(".code-swarm/agents.json")
    tasks_file = Path(".code-swarm/tasks.json")
    
    agents = []
    tasks = []
    if agents_file.exists():
        agents = json.loads(agents_file.read_text())
    if tasks_file.exists():
        tasks = json.loads(tasks_file.read_text())
    
    table = Table(title="Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    
    for agent in agents:
        table.add_row(
            agent.get("name", ""),
            agent.get("model", ""),
            agent.get("role", ""),
            agent.get("status", "")
        )
    
    console.print(table)
    console.print(f"\n[dim]Total Agents: {len(agents)} | Total Tasks: {len(tasks)}[/dim]")


@app.command()
def agents():
    agents_file = Path(".code-swarm/agents.json")
    if not agents_file.exists():
        console.print("[red]No agents found[/red]")
        return
    
    agents = json.loads(agents_file.read_text())
    
    table = Table(title="Code-Swarm Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for agent in agents:
        table.add_row(
            agent.get("name", ""),
            agent.get("model", ""),
            agent.get("role", ""),
            agent.get("status", ""),
            agent.get("created_at", "")[:10]
        )
    
    console.print(table)


@app.command()
def tasks(status: str = typer.Option(None, help="Filter by status")):
    tasks_file = Path(".code-swarm/tasks.json")
    if not tasks_file.exists():
        console.print("[red]No tasks found[/red]")
        return
    
    tasks = json.loads(tasks_file.read_text())
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    
    table = Table(title=f"Code-Swarm Tasks{f' ({status})' if status else ''}")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Priority", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Assigned To", style="magenta")
    
    for task in tasks:
        table.add_row(
            task.get("id", ""),
            task.get("title", "")[:30],
            str(task.get("priority", "")),
            task.get("status", ""),
            task.get("assigned_to", "unassigned")
        )
    
    console.print(table)


@app.command()
def run(task: str):
    console.print(f"[cyan]Running task:[/cyan] {task}")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        work = progress.add_task("[cyan]Processing...", total=100)
        for i in range(100):
            progress.update(work, advance=1)
    console.print("[green]Task completed![/green]")


if __name__ == "__main__":
    app()