from __future__ import annotations
import logging
import grpc
from concurrent import futures
import time
from pathlib import Path

import code_swarm_pb2
import code_swarm_pb2_grpc

# Import data utilities directly to avoid circular imports
from pathlib import Path
import json
import asyncio
import logging

# Import WebSocket broadcasting function from main module
# This will be set after the gRPC server is initialized to avoid circular imports
broadcast_agent_status = None

def _load_agents():
    agents_file = Path(".code-swarm/agents.json")
    if agents_file.exists():
        return json.loads(agents_file.read_text())
    return []

def _save_agents(agents):
    agents_file = Path(".code-swarm/agents.json")
    agents_file.parent.mkdir(parents=True, exist_ok=True)
    agents_file.write_text(json.dumps(agents, indent=2))

def _load_tasks():
    tasks_file = Path(".code-swarm/tasks.json")
    if tasks_file.exists():
        return json.loads(tasks_file.read_text())
    return []

def _save_tasks(tasks):
    tasks_file = Path(".code-swarm/tasks.json")
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(json.dumps(tasks, indent=2))
from datetime import datetime, timezone


class CodeSwarmAgentService(code_swarm_pb2_grpc.AgentServiceServicer):
    """gRPC service for agent operations."""

    def CreateAgent(self, request, context):
        agents_data = _load_agents()
        
        # Check if agent already exists
        for a in agents_data:
            if a["name"] == request.name:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("Agent already exists")
                return code_swarm_pb2.AgentResponse()
        
        new_agent = {
            "id": f"agent_{len(agents_data)+1}",
            "name": request.name,
            "model": request.model,
            "role": request.role,
            "capabilities": list(request.capabilities) if request.capabilities else [],
            "status": "idle",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        agents_data.append(new_agent)
        _save_agents(agents_data)
        
        return code_swarm_pb2.AgentResponse(**new_agent)

    def ListAgents(self, request, context):
        agents = _load_agents()
        
        if request.role:
            agents = [a for a in agents if a["role"] == request.role]
        
        return code_swarm_pb2.ListAgentsResponse(
            agents=[code_swarm_pb2.AgentResponse(**a) for a in agents]
        )

    def GetAgent(self, request, context):
        agents = _load_agents()
        for agent in agents:
            if agent["id"] == request.id:
                # Broadcast agent status update
                if broadcast_agent_status:
                    asyncio.run_coroutine_threadsafe(
                        broadcast_agent_status(
                            agent["id"],
                            agent["status"],
                            {"action": "get_agent", "status": "success"}
                        ),
                        asyncio.get_event_loop()
                    )
                return code_swarm_pb2.AgentResponse(
                    id=agent["id"],
                    name=agent["name"],
                    model=agent["model"],
                    role=agent["role"],
                    status=agent["status"],
                    created_at=agent["created_at"]
                )
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Agent not found")
        return code_swarm_pb2.AgentResponse()


class CodeSwarmTaskService(code_swarm_pb2_grpc.TaskServiceServicer):
    """gRPC service for task operations."""

    def CreateTask(self, request, context):
        tasks_data = _load_tasks()
        
        new_task = {
            "id": f"task_{len(tasks_data)+1}",
            "title": request.title,
            "description": request.description,
            "priority": request.priority,
            "assigned_to": request.assigned_to,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        tasks_data.append(new_task)
        _save_tasks(tasks_data)
        
        return code_swarm_pb2.TaskResponse(**new_task)

    def ListTasks(self, request, context):
        tasks = _load_tasks()
        
        if request.status:
            tasks = [t for t in tasks if t["status"] == request.status]
        
        return code_swarm_pb2.ListTasksResponse(
            tasks=[code_swarm_pb2.TaskResponse(**t) for t in tasks]
        )

    def UpdateTask(self, request, context):
        tasks = _load_tasks()
        
        for task in tasks:
            if task["id"] == request.id:
                task["status"] = request.status
                _save_tasks(tasks)
                return code_swarm_pb2.TaskResponse(**task)
        
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Task not found")
        return code_swarm_pb2.TaskResponse()


class CodeSwarmServer:
    """gRPC Server for Code-Swarm services."""

    def __init__(self, port: int = 50051):
        self.port = port
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Register services
        code_swarm_pb2_grpc.add_AgentServiceServicer_to_server(
            CodeSwarmAgentService(), self.server
        )
        code_swarm_pb2_grpc.add_TaskServiceServicer_to_server(
            CodeSwarmTaskService(), self.server
        )

    def start(self, max_retries: int = 3, retry_delay: int = 5):
        """Start the gRPC server with retries."""
        addr = f"[::]:{self.port}"
        self.server.add_insecure_port(addr)
        
        try:
            self.server.start()
            logging.info(f"gRPC server started on {self.port}")
            
            # Health check
            health_endpoint = Path(".code-swarm/grpc_health")
            health_endpoint.parent.mkdir(parents=True, exist_ok=True)
            health_endpoint.write_text(f"OK|grpc_server|{self.port}")
            
            logging.info(f"gRPC health endpoint created at {health_endpoint}")
            
        except Exception as e:
            logging.error(f"Failed to start gRPC server: {e}")
            raise

    def stop(self):
        """Stop the gRPC server."""
        self.server.stop(0)
        logging.info("gRPC server stopped")