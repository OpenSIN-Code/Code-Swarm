#!/usr/bin/env python3
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/jeremy/dev/Code-Swarm')

import grpc
from api import code_swarm_pb2, code_swarm_pb2_grpc
import threading
import time

class CodeSwarmTestClient:
    def __init__(self, port=50051):
        self.port = port
        self.channel = grpc.insecure_channel(f'localhost:{port}')
        self.agent_stub = code_swarm_pb2_grpc.AgentServiceStub(self.channel)
        self.task_stub = code_swarm_pb2_grpc.TaskServiceStub(self.channel)

    def test_agent_service(self):
        try:
            # Test GetAgent
            response = self.agent_stub.GetAgent(code_swarm_pb2.GetAgentRequest(id='sin-zeus'))
            print(f'GetAgent response: {response}')
            
            # Test ListAgents
            response = self.agent_stub.ListAgents(code_swarm_pb2.ListAgentsRequest())
            print(f'ListAgents response: {response}')
            
            return True
        except Exception as e:
            print(f'AgentService test failed: {e}')
            return False

def start_server():
    from api.grpc_server import CodeSwarmServer
    server = CodeSwarmServer(port=50051)
    server.start()
    print('gRPC server started on port 50051')
    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()

if __name__ == '__main__':
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    # Run client tests
    client = CodeSwarmTestClient()
    success = client.test_agent_service()
    
    if success:
        print('✅ gRPC integration test PASSED')
    else:
        print('❌ gRPC integration test FAILED')
        sys.exit(1)