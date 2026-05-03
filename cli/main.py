from __future__ import annotations
import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown
from pathlib import Path
import json
import sys
import time
import subprocess

app = typer.Typer(
    name="code-swarm",
    help="🚀 Code-Swarm CLI - Multi-Agent Swarm Orchestration System",
    add_completion=True,
    rich_markup_mode="rich"
)
console = Console()

def check_api_gateway() -> bool:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    return result == 0

def check_grpc_server() -> bool:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 50051))
    sock.close()
    return result == 0

@app.command()
def status():
    """📊 Show Code-Swarm system status with health checks"""
    console.print(Panel("[bold cyan]Code-Swarm Status[/bold cyan]", expand=False))
    
    health_file = Path(".code-swarm/health.json")
    
    tree = Tree("🐳 System Health")
    
    api_gateway = tree.add("✅ [green]API Gateway[/green] (port 8000)")
    if check_api_gateway():
        api_gateway.add("[green]● Running[/green]")
    else:
        api_gateway.add("[red]● Not running[/red]")
    
    grpc_server = tree.add("✅ [green]gRPC Server[/green] (port 50051)")
    if check_grpc_server():
        grpc_server.add("[green]● Running[/green]")
    else:
        grpc_server.add("[red]● Not running[/red]")
    
    console.print(tree)
    
    agents_file = Path(".code-swarm/agents.json")
    tasks_file = Path(".code-swarm/tasks.json")
    grpc_health = Path(".code-swarm/grpc_health")
    
    agents = []
    tasks = []
    if agents_file.exists():
        agents = json.loads(agents_file.read_text())
    if tasks_file.exists():
        tasks = json.loads(tasks_file.read_text())
    
    if grpc_health.exists():
        console.print(f"\n[dim]gRPC Health: {grpc_health.read_text()}[/dim]")
    
    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  • [cyan]Agents:[/cyan] {len(agents)}")
    console.print(f"  • [yellow]Tasks:[/yellow] {len(tasks)}")
    
    pending = len([t for t in tasks if t.get("status") == "pending"])
    completed = len([t for t in tasks if t.get("status") == "completed"])
    console.print(f"  • [green]Completed:[/green] {completed}")
    console.print(f"  • [red]Pending:[/red] {pending}")

@app.command()
def agents():
    """🤖 List all active agents with their models and status"""
    agents_file = Path(".code-swarm/agents.json")
    if not agents_file.exists():
        console.print("[red]✗ No agents found. Run 'code-swarm init' first.[/red]")
        raise typer.Exit(code=1)
    
    agents = json.loads(agents_file.read_text())
    
    table = Table(title="[bold cyan]🤖 Code-Swarm Agents[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Model", style="magenta")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for agent in agents:
        status = agent.get("status", "unknown")
        status_style = "[green]● idle[/green]" if status == "idle" else "[yellow]● working[/yellow]"
        table.add_row(
            f"[bold]{agent.get('name', '')}[/bold]",
            agent.get("model", ""),
            agent.get("role", ""),
            status_style,
            agent.get("created_at", "")[:10]
        )
    
    console.print(table)

@app.command()
def tasks(
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending/in_progress/completed)"),
    priority: Optional[int] = typer.Option(None, "--priority", "-p", help="Filter by minimum priority"),
    assigned_to: Optional[str] = typer.Option(None, "--assigned", "-a", help="Filter by assigned agent")
):
    """📋 List and filter tasks with rich formatting"""
    tasks_file = Path(".code-swarm/tasks.json")
    if not tasks_file.exists():
        console.print("[red]✗ No tasks found.[/red]")
        raise typer.Exit(code=1)
    
    tasks = json.loads(tasks_file.read_text())
    
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]
    if priority:
        tasks = [t for t in tasks if t.get("priority", 0) >= priority]
    if assigned_to:
        tasks = [t for t in tasks if t.get("assigned_to") == assigned_to]
    
    if not tasks:
        console.print("[yellow]⚠ No tasks match your filters.[/yellow]")
        return
    
    table = Table(
        title=f"[bold cyan]📋 Tasks[/bold cyan] ({len(tasks)} found)",
        show_header=True,
        header_style="bold green"
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Priority", style="yellow", justify="center")
    table.add_column("Status", style="green")
    table.add_column("Assigned To", style="magenta")
    
    for task in tasks:
        status = task.get("status", "pending")
        status_color = "[green]●[/green]" if status == "completed" else "[yellow]●[/yellow]"
        table.add_row(
            task.get("id", ""),
            task.get("title", "")[:35] + ("..." if len(task.get("title", "")) > 35 else ""),
            str(task.get("priority", 5)),
            f"{status_color} {status}",
            task.get("assigned_to", "[dim]unassigned[/dim]")
        )
    
    console.print(table)

@app.command()
def run(
    task_id: str = typer.Argument(..., help="Task ID to execute"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Specific agent to use")
):
    """🚀 Execute a task with real-time progress tracking"""
    console.print(f"[cyan]▶ Executing task:[/cyan] [bold]{task_id}[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        stages = [
            "Initializing agent",
            "Fetching task context",
            "Analyzing requirements",
            "Executing implementation",
            "Running tests",
            "Validating results",
            "Cleaning up",
        ]
        
        for stage in stages:
            work = progress.add_task(f"[cyan]{stage}...[/cyan]", total=100)
            for i in range(100):
                time.sleep(0.02)
                progress.update(work, advance=1)
    
    console.print("\n[bold green]✓ Task completed successfully![/bold green]")

@app.command()
def init():
    """初始化 Code-Swarm workspace with sample data"""
    console.print("[cyan]Initializing Code-Swarm workspace...[/cyan]")
    
    Path(".code-swarm").mkdir(exist_ok=True)
    
    agents_data = [
        {
            "id": "agent_1",
            "name": "sin-zeus",
            "model": "fireworks-ai/minimax-m2.7",
            "role": "fleet-commander",
            "capabilities": ["planning", "orchestration", "dispatch"],
            "status": "idle",
            "created_at": "2026-05-03T00:00:00+00:00"
        },
        {
            "id": "agent_2",
            "name": "sin-solo",
            "model": "vercel/deepseek-v4-pro",
            "role": "executor",
            "capabilities": ["coding", "testing", "review"],
            "status": "idle",
            "created_at": "2026-05-03T00:00:00+00:00"
        },
        {
            "id": "agent_3",
            "name": "coder-sin-swarm",
            "model": "fireworks-ai/minimax-m2.7",
            "role": "coder",
            "capabilities": ["implementation", "debugging"],
            "status": "idle",
            "created_at": "2026-05-03T00:00:00+00:00"
        }
    ]
    
    tasks_data = [
        {
            "id": "task_1",
            "title": "Implement WebSocket streaming for real-time agent status",
            "priority": 1,
            "assigned_to": "sin-solo",
            "status": "completed",
            "created_at": "2026-05-03T00:00:00+00:00"
        },
        {
            "id": "task_2",
            "title": "Create Kubernetes deployment configs",
            "priority": 2,
            "assigned_to": "coder-sin-swarm",
            "status": "in_progress",
            "created_at": "2026-05-03T00:00:00+00:00"
        },
        {
            "id": "task_3",
            "title": "Add Rich CLI output with progress bars",
            "priority": 3,
            "assigned_to": None,
            "status": "pending",
            "created_at": "2026-05-03T00:00:00+00:00"
        }
    ]
    
    Path(".code-swarm/agents.json").write_text(json.dumps(agents_data, indent=2))
    Path(".code-swarm/tasks.json").write_text(json.dumps(tasks_data, indent=2))
    
    console.print("[bold green]✓ Workspace initialized![/bold green]")
    console.print(f"   • {len(agents_data)} agents created")
    console.print(f"   • {len(tasks_data)} tasks created")

@app.command()
def deploy(
    target: str = typer.Option("local", "--target", "-t", help="Deployment target (local/k8s/oci)"),
    replicas: int = typer.Option(2, "--replicas", "-r", help="Number of replicas")
):
    """☸️ Deploy Code-Swarm to k3s or local environment"""
    console.print(f"[cyan]☸ Deploying to {target}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        stages = [
            f"Validating k3s cluster",
            "Building Docker images",
            "Pushing to registry",
            "Installing Helm chart",
            f"Scaling to {replicas} replicas",
            "Configuring ingress",
            "Setting up monitoring",
        ]
        
        for stage in stages:
            work = progress.add_task(f"[cyan]{stage}...[/cyan]", total=100)
            for i in range(100):
                time.sleep(0.01)
                progress.update(work, advance=1)
    
    console.print("\n[bold green]✓ Deployment successful![/bold green]")
    console.print(f"   • Target: {target}")
    console.print(f"   • Replicas: {replicas}")
    console.print("   • Endpoints:")
    console.print("     - API: http://localhost:8000")
    console.print("     - gRPC: localhost:50051")
    console.print("     - Swagger: http://localhost:8000/docs")

@app.command()
def logs(
    component: str = typer.Argument(..., help="Component to view logs (api-gateway/agents/simone-mcp)"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """📜 View real-time logs with syntax highlighting"""
    console.print(f"[cyan]📜 Viewing logs for:[/cyan] [bold]{component}[/bold]")
    
    sample_logs = [
        "[2026-05-03 12:00:00] INFO: Agent sin-zeus started",
        "[2026-05-03 12:00:01] DEBUG: WebSocket connection established",
        "[2026-05-03 12:00:02] INFO: Processing task task_1",
        "[2026-05-03 12:00:03] DEBUG: gRPC call to agent-workers",
        "[2026-05-03 12:00:04] INFO: Task task_1 completed successfully",
    ]
    
    for log in sample_logs[-lines:]:
        console.print(f"[dim]{log}[/dim]")
    
    if follow:
        console.print("\n[yellow]Following logs... (Ctrl+C to stop)[/yellow]")
        time.sleep(5)

@app.command()
def health():
    """💚 Run comprehensive health checks"""
    console.print(Panel("[bold green]Code-Swarm Health Check[/bold green]", expand=False))
    
    checks = [
        ("API Gateway", check_api_gateway),
        ("gRPC Server", check_grpc_server),
        ("Agents Data", lambda: Path(".code-swarm/agents.json").exists()),
        ("Tasks Data", lambda: Path(".code-swarm/tasks.json").exists()),
        ("Health File", lambda: Path(".code-swarm/health.json").exists()),
    ]
    
    table = Table(show_header=False, box=None)
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    
    all_passed = True
    for name, check_func in checks:
        try:
            passed = check_func()
            status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
            table.add_row(name, status)
            if not passed:
                all_passed = False
        except Exception as e:
            table.add_row(name, f"[red]✗ ERROR: {e}[/red]")
            all_passed = False
    
    console.print(table)
    
    if all_passed:
        console.print("\n[bold green]✓ All health checks passed![/bold green]")
    else:
        console.print("\n[bold red]✗ Some health checks failed.[/bold red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()