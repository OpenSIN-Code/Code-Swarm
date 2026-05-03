from __future__ import annotations
import typer
from typing import Optional, List
import shlex
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn, track
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.align import Align
from rich.text import Text
from pathlib import Path
import json
import sys
import time
import subprocess
import requests
import os
from datetime import datetime

from .recursivemas import (
    benchmark_rows,
    build_run_command,
    format_style_summary,
    list_supported_styles,
    missing_runtime_dependencies,
)

app = typer.Typer(
    name="code-swarm",
    help="🚀 Code-Swarm CLI - Multi-Agent Swarm Orchestration System",
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True
)

mas_app = typer.Typer(
    name="mas",
    help="RecursiveMAS integration commands",
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
)

app.add_typer(mas_app, name="mas")

console = Console()
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def check_api_gateway() -> bool:
    """Check if API gateway is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def check_grpc_server() -> bool:
    """Check if gRPC server is running."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 50051))
    sock.close()
    return result == 0


def get_api_token() -> Optional[str]:
    """Get API token from environment or cache."""
    token = os.getenv("CODE_SWARM_TOKEN")
    if not token:
        token_file = Path.home() / ".code-swarm" / "token"
        if token_file.exists():
            token = token_file.read_text().strip()
    return token


def save_api_token(token: str):
    """Save API token to cache."""
    token_file = Path.home() / ".code-swarm" / "token"
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)
    token_file.chmod(0o600)


def api_get(endpoint: str, headers: Optional[dict] = None) -> dict:
    """Make GET request to API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        h = {"Authorization": f"Bearer {get_api_token()}"} if not headers else headers
        response = requests.get(url, headers=h, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[red]✗ API Error: {e}[/red]")
        raise typer.Exit(code=1)


def api_post(endpoint: str, data: dict, headers: Optional[dict] = None) -> dict:
    """Make POST request to API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        h = {"Authorization": f"Bearer {get_api_token()}"} if not headers else headers
        response = requests.post(url, json=data, headers=h, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[red]✗ API Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def status():
    """📊 Show Code-Swarm system status with health checks"""
    console.print(Panel("[bold cyan]Code-Swarm Status[/bold cyan]", expand=False))
    
    tree = Tree("🐳 System Health")
    
    # API Gateway
    api_running = check_api_gateway()
    api_status = tree.add("[green]✓ API Gateway[/green]" if api_running else "[red]✗ API Gateway[/red]")
    api_status.add(f"[green]● Running[/green] ({API_BASE_URL})" if api_running else "[red]● Stopped[/red]")
    
    # gRPC Server
    grpc_running = check_grpc_server()
    grpc_status = tree.add("[green]✓ gRPC Server[/green]" if grpc_running else "[red]✗ gRPC Server[/red]")
    grpc_status.add("[green]● Running[/green] (localhost:50051)" if grpc_running else "[red]● Stopped[/red]")
    
    console.print(tree)
    
    # API Statistics
    if api_running:
        try:
            stats = api_get("/metrics")
            console.print(f"\n[bold cyan]Statistics:[/bold cyan]")
            console.print(f"  • [cyan]Agents:[/cyan] {stats.get('metrics', {}).get('total_agents', 0)}")
            console.print(f"  • [yellow]Tasks:[/yellow] {stats.get('metrics', {}).get('total_tasks', 0)}")
            console.print(f"  • [green]Avg Task Duration:[/green] {stats.get('metrics', {}).get('avg_task_duration', 'N/A')}")
        except Exception:
            pass


@app.command()
def agents(
    role: Optional[str] = typer.Option(None, "--role", help="Filter by agent role"),
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status")
):
    """🤖 List all active agents with details"""
    try:
        agents_data = api_get("/agents")
        
        # Filter
        if role:
            agents_data = [a for a in agents_data if a.get("role") == role]
        if status_filter:
            agents_data = [a for a in agents_data if a.get("status") == status_filter]
        
        if not agents_data:
            console.print("[yellow]No agents found[/yellow]")
            return
        
        # Table
        table = Table(title=f"[bold cyan]🤖 Agents ({len(agents_data)})[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Role", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="dim")
        
        for agent in agents_data:
            status_icon = "🟢" if agent.get("status") == "active" else "⚪"
            table.add_row(
                agent.get("id", "N/A"),
                agent.get("name", "N/A"),
                agent.get("model", "N/A"),
                agent.get("role", "N/A"),
                f"{status_icon} {agent.get('status', 'N/A')}",
                agent.get("created_at", "N/A")[:10]
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def tasks(
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status (pending, active, completed)")
):
    """📋 List all tasks with status"""
    try:
        tasks_data = api_get("/tasks")
        
        if status_filter:
            tasks_data = [t for t in tasks_data if t.get("status") == status_filter]
        
        if not tasks_data:
            console.print("[yellow]No tasks found[/yellow]")
            return
        
        # Table
        table = Table(title=f"[bold cyan]📋 Tasks ({len(tasks_data)})[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Priority", style="red")
        table.add_column("Assigned", style="green")
        table.add_column("Created", style="dim")
        
        for task in tasks_data:
            status_icon = "🟢" if task.get("status") == "completed" else "🟡" if task.get("status") == "active" else "⚪"
            table.add_row(
                task.get("id", "N/A"),
                task.get("title", "N/A")[:40],
                f"{status_icon} {task.get('status', 'N/A')}",
                str(task.get("priority", "N/A")),
                task.get("assigned_to", "Unassigned"),
                task.get("created_at", "N/A")[:10]
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def create_task(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--desc", help="Task description"),
    priority: int = typer.Option(5, "--priority", min=1, max=10, help="Priority 1-10"),
    assigned_to: Optional[str] = typer.Option(None, "--assign", help="Assign to agent")
):
    """➕ Create a new task"""
    try:
        task_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "assigned_to": assigned_to
        }
        
        with console.status("[bold cyan]Creating task...[/bold cyan]"):
            result = api_post("/tasks", task_data)
        
        console.print(f"[green]✓ Task created: {result.get('id')}[/green]")
        console.print(Panel(
            f"[cyan]Title:[/cyan] {result.get('title')}\n"
            f"[yellow]Status:[/yellow] {result.get('status')}\n"
            f"[magenta]Priority:[/magenta] {result.get('priority')}/10",
            title="[bold]Task Details[/bold]"
        ))
    except Exception as e:
        console.print(f"[red]✗ Error creating task: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def create_agent(
    name: str = typer.Argument(..., help="Agent name"),
    model: str = typer.Option("gpt-4", "--model", help="Model to use"),
    role: str = typer.Option("backend", "--role", help="Agent role"),
    capabilities: Optional[str] = typer.Option(None, "--cap", help="Comma-separated capabilities")
):
    """➕ Create a new agent"""
    try:
        agent_data = {
            "name": name,
            "model": model,
            "role": role,
            "capabilities": capabilities.split(",") if capabilities else []
        }
        
        with console.status("[bold cyan]Creating agent...[/bold cyan]"):
            result = api_post("/agents", agent_data)
        
        console.print(f"[green]✓ Agent created: {result.get('id')}[/green]")
        console.print(Panel(
            f"[cyan]Name:[/cyan] {result.get('name')}\n"
            f"[magenta]Model:[/magenta] {result.get('model')}\n"
            f"[green]Role:[/green] {result.get('role')}",
            title="[bold]Agent Details[/bold]"
        ))
    except Exception as e:
        console.print(f"[red]✗ Error creating agent: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def login(
    username: str = typer.Argument(..., help="Username"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="Password")
):
    """🔐 Login to Code-Swarm and save token"""
    try:
        with console.status("[bold cyan]Authenticating...[/bold cyan]"):
            response = requests.post(
                f"{API_BASE_URL}/auth/token",
                json={"username": username, "password": password},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        token = data.get("access_token")
        save_api_token(token)
        console.print(f"[green]✓ Logged in as {username}[/green]")
        console.print(f"[dim]Token saved to ~/.code-swarm/token[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def health():
    """🏥 Perform comprehensive health check"""
    console.print(Panel("[bold cyan]Health Check[/bold cyan]", expand=False))
    
    checks = [
        ("API Gateway", lambda: requests.get(f"{API_BASE_URL}/health", timeout=2)),
        ("Database", lambda: api_get("/metrics")),
        ("gRPC Server", lambda: check_grpc_server())
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for check_name, check_func in checks:
            task = progress.add_task(f"Checking {check_name}...", total=None)
            try:
                result = check_func()
                progress.update(task, description=f"[green]✓ {check_name}[/green]")
            except Exception as e:
                progress.update(task, description=f"[red]✗ {check_name}: {e}[/red]")
            time.sleep(0.5)


@mas_app.command("styles")
def mas_styles():
    """📚 List supported RecursiveMAS styles."""
    table = Table(
        title=f"[bold cyan]RecursiveMAS Styles[/bold cyan] ({len(benchmark_rows())} benchmarks)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Style", style="cyan")
    table.add_column("Family", style="green")
    table.add_column("Batch", style="yellow", justify="right")
    table.add_column("Description", style="white")

    for style in list_supported_styles():
        summary = format_style_summary(style).splitlines()
        family = next((line.split(": ", 1)[1] for line in summary if line.startswith("Family:")), "n/a")
        batch = next((line.split(": ", 1)[1] for line in summary if line.startswith("Recommended batch size:")), "n/a")
        description = next((line.split(": ", 1)[1] for line in summary if line.startswith("Description:")), "n/a")
        table.add_row(style, family, batch, description)

    console.print(table)


@mas_app.command("inspect")
def mas_inspect(
    style: str = typer.Argument(..., help="RecursiveMAS style name")
):
    """🔎 Show the role layout and checkpoint mapping for a style."""
    console.print(Panel(format_style_summary(style), title=f"[bold]RecursiveMAS: {style}[/bold]", expand=False))


@mas_app.command("benchmark")
def mas_benchmark(
    style: str = typer.Argument(..., help="RecursiveMAS style name"),
    dataset: str = typer.Option("math500", "--dataset", help="Benchmark dataset"),
    dataset_split: str = typer.Option("", "--dataset-split", help="Override dataset split"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", help="Override batch size"),
    latent_length: int = typer.Option(32, "--latent-length", help="Latent recursion steps"),
    rounds: int = typer.Option(3, "--rounds", help="Recursive rounds"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    sample_seed: int = typer.Option(-1, "--sample-seed", help="Sampling seed"),
    temperature: float = typer.Option(0.6, "--temperature", help="Sampling temperature"),
    top_p: float = typer.Option(0.95, "--top-p", help="Top-p sampling"),
    top_k: int = typer.Option(-1, "--top-k", help="Top-k sampling"),
    device: Optional[str] = typer.Option(None, "--device", help="Torch device"),
    trust_remote_code: bool = typer.Option(True, "--trust-remote-code/--no-trust-remote-code", help="Trust HF repo code"),
    python: str = typer.Option(sys.executable, "--python", help="Python executable"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print command only"),
):
    """🧪 Run the RecursiveMAS benchmark runner."""
    missing = missing_runtime_dependencies()
    command = build_run_command(
        style,
        dataset=dataset,
        dataset_split=dataset_split,
        batch_size=batch_size,
        device=device,
        seed=seed,
        sample_seed=sample_seed,
        rounds=rounds,
        latent_length=latent_length,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        trust_remote_code=trust_remote_code,
        python_executable=python,
    )

    console.print(Panel(shlex.join(command), title="[bold]RecursiveMAS command[/bold]", expand=False))

    if dry_run:
        if missing:
            console.print(f"[yellow]Missing runtime deps:[/yellow] {', '.join(missing)}")
        return

    if missing:
        console.print(
            Panel(
                "\n".join(
                    [
                        "RecursiveMAS runtime dependencies are missing.",
                        f"Missing: {', '.join(missing)}",
                        "Install recursivemas/requirements.txt before running the benchmark.",
                    ]
                ),
                title="[red]Dependency Check Failed[/red]",
                expand=False,
            )
        )
        raise typer.Exit(code=1)

    completed = subprocess.run(command)
    if completed.returncode != 0:
        raise typer.Exit(code=completed.returncode)


if __name__ == "__main__":
    app()
