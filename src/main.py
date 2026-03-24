import os
import sys
import time
import random
import multiprocessing as mp

from swarm_orchestrator.agent import Agent
from swarm_orchestrator.coordinator import Coordinator
from swarm_orchestrator.communication import Message, MessageBus

def main():
    """Main entry point for the Swarm Orchestrator application."""
    # Initialize the message bus
    message_bus = MessageBus()

    # Create the coordinator process
    coordinator = Coordinator(message_bus)
    coordinator_process = mp.Process(target=coordinator.run)
    coordinator_process.start()

    # Create and register agent processes
    agents = []
    for _ in range(10):
        agent = Agent(message_bus)
        agent_process = mp.Process(target=agent.run)
        agent_process.start()
        agents.append(agent_process)

    # Wait for the coordinator and agents to finish
    coordinator_process.join()
    for agent in agents:
        agent.join()

if __name__ == "__main__":
    main()