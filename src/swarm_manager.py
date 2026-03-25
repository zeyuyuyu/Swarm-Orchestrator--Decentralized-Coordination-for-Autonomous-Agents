import logging
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SwarmNode:
    id: str
    status: str  # 'active', 'failed', 'recovering'
    last_heartbeat: float
    workload: int
    capacity: int

class SwarmManager:
    def __init__(self):
        self.nodes: Dict[str, SwarmNode] = {}
        self.lock = threading.Lock()
        self.heartbeat_interval = 5.0
        self.heartbeat_timeout = 15.0
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('SwarmManager')
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_nodes, daemon=True)
        self._monitor_thread.start()

    def register_node(self, node_id: str, capacity: int) -> bool:
        with self.lock:
            if node_id in self.nodes:
                self.logger.warning(f'Node {node_id} already registered')
                return False
                
            self.nodes[node_id] = SwarmNode(
                id=node_id,
                status='active',
                last_heartbeat=time.time(),
                workload=0,
                capacity=capacity
            )
            self.logger.info(f'Node {node_id} registered with capacity {capacity}')
            return True

    def heartbeat(self, node_id: str) -> bool:
        with self.lock:
            if node_id not in self.nodes:
                return False
            self.nodes[node_id].last_heartbeat = time.time()
            if self.nodes[node_id].status == 'failed':
                self.nodes[node_id].status = 'recovering'
            return True

    def assign_work(self, work_units: int) -> Optional[str]:
        with self.lock:
            available_nodes = [
                node for node in self.nodes.values()
                if node.status == 'active' and node.workload < node.capacity
            ]
            
            if not available_nodes:
                return None

            # Find node with most available capacity
            best_node = min(
                available_nodes,
                key=lambda n: n.workload / n.capacity
            )

            if best_node.workload + work_units <= best_node.capacity:
                best_node.workload += work_units
                self.logger.info(f'Assigned {work_units} units to node {best_node.id}')
                return best_node.id
            
            return None

    def complete_work(self, node_id: str, work_units: int) -> bool:
        with self.lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            node.workload = max(0, node.workload - work_units)
            self.logger.info(f'Node {node_id} completed {work_units} units')
            return True

    def _monitor_nodes(self):
        while True:
            time.sleep(self.heartbeat_interval)
            with self.lock:
                current_time = time.time()
                for node in self.nodes.values():
                    if current_time - node.last_heartbeat > self.heartbeat_timeout:
                        if node.status != 'failed':
                            node.status = 'failed'
                            self.logger.warning(f'Node {node.id} marked as failed')
                            self._redistribute_work(node)

    def _redistribute_work(self, failed_node: SwarmNode):
        work_to_reassign = failed_node.workload
        failed_node.workload = 0
        
        while work_to_reassign > 0:
            assigned_node_id = self.assign_work(1)
            if assigned_node_id is None:
                self.logger.error(f'Unable to redistribute {work_to_reassign} remaining work units')
                break
            work_to_reassign -= 1

    def get_swarm_status(self) -> Dict:
        with self.lock:
            return {
                'total_nodes': len(self.nodes),
                'active_nodes': sum(1 for n in self.nodes.values() if n.status == 'active'),
                'failed_nodes': sum(1 for n in self.nodes.values() if n.status == 'failed'),
                'total_capacity': sum(n.capacity for n in self.nodes.values()),
                'total_workload': sum(n.workload for n in self.nodes.values()),
                'nodes': {
                    nid: {
                        'status': n.status,
                        'workload': n.workload,
                        'capacity': n.capacity
                    } for nid, n in self.nodes.items()
                }
            }