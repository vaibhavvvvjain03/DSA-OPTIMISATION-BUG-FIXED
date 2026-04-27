import time
import random

# HIDDEN BUG: Memory Leak
# This list will keep growing and never gets cleared, causing OOM eventually in huge simulations
GLOBAL_AUDIT_LOGS = []

class DeliveryEngineSuboptimal:
    def __init__(self, city_nodes=100):
        # BUG: Adjacency Matrix uses O(V^2) space and is slow for sparse graphs
        self.graph = [[0] * city_nodes for _ in range(city_nodes)]
        self.orders = [] # O(N) lookup time, should be a hashmap
        self.addresses = [] # Linear search for autocomplete
        self.nodes_count = city_nodes

    def add_edge(self, u, v, weight):
        # Sparse city updates are slow in matrix
        self.graph[u][v] = weight
        self.graph[v][u] = weight

    def add_address(self, address):
        self.addresses.append(address)

    def autocomplete(self, query):
        # BUG: O(N*M) - Linear scan over all addresses
        # Should use a TRIE
        results = []
        for addr in self.addresses:
            if addr.lower().startswith(query.lower()):
                results.append(addr)
        return results[:5]

    def add_order(self, order_id, priority):
        # BUG: O(N log N) every time an order is added
        # Should use a HEAP
        self.orders.append({'id': order_id, 'priority': priority})
        self.orders.sort(key=lambda x: x['priority'], reverse=True) # High priority first
        
        # Memory leak simulation
        GLOBAL_AUDIT_LOGS.append({'event': 'order_added', 'data': order_id, 'timestamp': time.time()})

    def get_highest_priority_order(self):
        # O(1) because we keep it sorted, but the cost was paid in add_order
        if not self.orders:
            return None
        return self.orders.pop(0)

    def find_order_by_id(self, order_id):
        # BUG: Linear Search O(N)
        # Should use a HASHMAP
        for order in self.orders:
            if order['id'] == order_id:
                return order
        return None

    def find_route(self, start_node, end_node):
        # BUG: Recursive BFS without "visited" set!
        # This will cause an Infinite Loop / Recursion Depth Error if there is a cycle
        # BUG: It doesn't find the shortest path, just A path.
        # Should use DIJKSTRA
        return self._recursive_pathfinding(start_node, end_node, [])

    def _recursive_pathfinding(self, current, target, path):
        path = path + [current]
        if current == target:
            return path
        
        # BFS simulation via recursion (very bad)
        for neighbor, weight in enumerate(self.graph[current]):
            if weight > 0:
                # Missing 'if neighbor not in path' - leads to infinite loop if graph has cycles
                new_path = self._recursive_pathfinding(neighbor, target, path)
                if new_path:
                    return new_path
        return None

def simulate_unoptimized(n_orders=1000):
    engine = DeliveryEngineSuboptimal(city_nodes=50)
    # Add some cyclic routes
    engine.add_edge(0, 1, 10)
    engine.add_edge(1, 2, 10)
    engine.add_edge(2, 0, 10) # Cycle
    
    start_time = time.time()
    
    # Simulation
    for i in range(n_orders):
        engine.add_order(f"ORD-{i}", random.randint(1, 100))
        
    # Search simulation
    for i in range(10):
        engine.find_order_by_id(f"ORD-{random.randint(0, n_orders-1)}")
        
    # ROUTE CALCULATION - WARNING: Might crash if cycle is hit
    try:
        engine.find_route(0, 2)
    except Exception as e:
        print(f"Algorithm failed as expected: {e}")
        
    return time.time() - start_time
