"""
Optimized Delivery Engine
=========================
Fixes all algorithmic bugs in DeliveryEngineSuboptimal:

  Bug Fixed                   | Suboptimal           | Optimized
  ----------------------------|----------------------|----------------------------
  Graph representation        | O(V^2) adj matrix    | O(V+E) adjacency list (dict)
  Order insertion             | O(N log N) re-sort   | O(log N) min-heap push
  Order lookup by ID          | O(N) linear scan     | O(1) hash-map lookup
  Address autocomplete        | O(N*M) linear scan   | O(M) Trie traversal
  Route finding               | Recursive BFS, no    | Iterative Dijkstra with
                              | visited set -> inf   | visited set, finds shortest
                              | loop on cycles       | path, handles cycles safely
  Memory leak                 | Unbounded global     | No global mutable state
                              | GLOBAL_AUDIT_LOGS    |
"""

import heapq
import collections


# ---------------------------------------------------------------------------
# TRIE — O(M) insert and O(M + K) prefix search (M = word length, K = results)
# ---------------------------------------------------------------------------

class _TrieNode:
    """Single node in a Trie."""
    __slots__ = ("children", "is_end")

    def __init__(self):
        self.children: dict[str, "_TrieNode"] = {}
        self.is_end: bool = False


class Trie:
    """
    Prefix tree for O(M) insert and autocomplete queries.

    Replaces the O(N*M) linear scan used by the suboptimal engine.
    """

    def __init__(self):
        self._root = _TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie in O(M) time."""
        node = self._root
        for ch in word.lower():
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search_prefix(self, prefix: str, limit: int = 5) -> list[str]:
        """
        Return up to *limit* words sharing the given prefix.

        Time complexity: O(M + K) where M = prefix length, K = result count.
        """
        node = self._root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]

        results: list[str] = []
        self._dfs(node, list(prefix.lower()), results, limit)
        return results

    def _dfs(self, node: _TrieNode, path: list[str], results: list[str], limit: int) -> None:
        """Depth-first traversal to collect words."""
        if len(results) >= limit:
            return
        if node.is_end:
            results.append("".join(path))
        for ch, child in node.children.items():
            path.append(ch)
            self._dfs(child, path, results, limit)
            path.pop()


# ---------------------------------------------------------------------------
# MIN-HEAP PRIORITY QUEUE — O(log N) push/pop
# ---------------------------------------------------------------------------

class _HeapOrder:
    """Wrapper for (priority, order_id) that supports heap comparison."""
    __slots__ = ("priority", "order_id")

    def __init__(self, priority: int, order_id: str):
        # Negate priority so that the *highest* numeric priority is popped first
        # (standard Python heapq is a min-heap).
        self.priority = -priority
        self.order_id = order_id

    def __lt__(self, other: "_HeapOrder") -> bool:
        return self.priority < other.priority

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _HeapOrder):
            return NotImplemented
        return self.priority == other.priority


# ---------------------------------------------------------------------------
# ADJACENCY LIST GRAPH — O(V+E) space, O(E log V) Dijkstra
# ---------------------------------------------------------------------------

class DeliveryEngineOptimized:
    """
    Production-quality delivery engine with correct algorithmic complexity.

    Provides the identical public API as DeliveryEngineSuboptimal so that
    app.py can swap between them without any other code changes.
    """

    def __init__(self):
        # O(V+E) adjacency list: {node: [(weight, neighbor), ...]}
        self._graph: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)

        # Min-heap for order dispatch: [(negated_priority, order_id), ...]
        self._order_heap: list[_HeapOrder] = []

        # O(1) lookup by order_id
        self._order_map: dict[str, int] = {}  # order_id -> priority

        # Trie for O(M) autocomplete
        self._address_trie = Trie()

    # ------------------------------------------------------------------
    # Graph API
    # ------------------------------------------------------------------

    def add_edge(self, u: int, v: int, weight: int) -> None:
        """
        Add an undirected weighted edge in O(1).

        Replaces the O(V^2) matrix assignment in the suboptimal engine.
        """
        self._graph[u].append((weight, v))
        self._graph[v].append((weight, u))

    # ------------------------------------------------------------------
    # Address autocomplete
    # ------------------------------------------------------------------

    def add_address(self, address: str) -> None:
        """Insert address into trie in O(M)."""
        self._address_trie.insert(address)

    def autocomplete(self, query: str) -> list[str]:
        """
        Return up to 5 addresses matching the given prefix.

        Time: O(M + K)  vs  O(N*M) in the suboptimal engine.
        """
        return self._address_trie.search_prefix(query, limit=5)

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    def add_order(self, order_id: str, priority: int) -> None:
        """
        Enqueue an order in O(log N).

        Replaces the O(N log N) full re-sort done on every insertion.
        No global audit log — no memory leak.
        """
        entry = _HeapOrder(priority, order_id)
        heapq.heappush(self._order_heap, entry)
        self._order_map[order_id] = priority

    def get_highest_priority_order(self) -> dict | None:
        """
        Pop and return the highest-priority order in O(log N).

        Handles lazy deletion: skips orders that were removed via the map.
        """
        while self._order_heap:
            entry = heapq.heappop(self._order_heap)
            oid = entry.order_id
            if oid in self._order_map:
                del self._order_map[oid]
                return {"id": oid, "priority": -entry.priority}
        return None

    def find_order_by_id(self, order_id: str) -> dict | None:
        """
        O(1) hash-map lookup.

        Replaces the O(N) linear scan in the suboptimal engine.
        """
        if order_id in self._order_map:
            return {"id": order_id, "priority": self._order_map[order_id]}
        return None

    # ------------------------------------------------------------------
    # Route finding — iterative Dijkstra
    # ------------------------------------------------------------------

    def find_route(self, start_node: int, end_node: int) -> list[int] | None:
        """
        Find the shortest-weight path using iterative Dijkstra.

        Fixes three bugs from the suboptimal engine:
          1. Uses a visited set -> no infinite loops on cycles.
          2. Iterative (not recursive) -> no RecursionDepthError.
          3. Finds the *shortest* path (by weight), not just any path.

        Time:  O((V + E) log V)
        Space: O(V)
        """
        if start_node not in self._graph and end_node not in self._graph:
            return None

        dist: dict[int, float] = collections.defaultdict(lambda: float("inf"))
        dist[start_node] = 0
        prev: dict[int, int | None] = {start_node: None}

        # heap entries: (cumulative_cost, node)
        heap: list[tuple[float, int]] = [(0, start_node)]
        visited: set[int] = set()

        while heap:
            cost, node = heapq.heappop(heap)

            if node in visited:
                continue
            visited.add(node)

            if node == end_node:
                break

            for weight, neighbor in self._graph[node]:
                new_cost = cost + weight
                if new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_cost, neighbor))

        if dist[end_node] == float("inf"):
            return None  # no path exists

        # Reconstruct path
        path: list[int] = []
        cursor: int | None = end_node
        while cursor is not None:
            path.append(cursor)
            cursor = prev.get(cursor)
        path.reverse()
        return path
