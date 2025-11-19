"""
DAG (Directed Acyclic Graph) utilities for dependency resolution.
"""

import logging
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)


class DAGCycleError(Exception):
    """Exception raised when a cycle is detected in the DAG."""
    pass


class DAGResolver:
    """
    Directed Acyclic Graph resolver for task dependency management.

    This class provides utilities for building and resolving task dependencies
    using topological sorting (Kahn's algorithm).
    """

    def __init__(self):
        """Initialize the DAG resolver."""
        self._graph: dict[Any, list[Any]] = defaultdict(list)
        self._in_degree: dict[Any, int] = defaultdict(int)
        self._nodes: set[Any] = set()

    def add_node(self, node: Any) -> None:
        """
        Add a node to the graph.

        Args:
            node: Node identifier
        """
        self._nodes.add(node)
        if node not in self._in_degree:
            self._in_degree[node] = 0

    def add_edge(self, from_node: Any, to_node: Any) -> None:
        """
        Add a directed edge from one node to another.

        Args:
            from_node: Source node
            to_node: Target node (depends on source)
        """
        self.add_node(from_node)
        self.add_node(to_node)

        self._graph[from_node].append(to_node)
        self._in_degree[to_node] += 1

    def topological_sort(self) -> list[Any]:
        """
        Perform topological sort on the graph.

        Returns:
            List of nodes in topological order

        Raises:
            DAGCycleError: If a cycle is detected in the graph
        """
        if not self._nodes:
            return []

        # Create working copies
        in_degree = dict(self._in_degree)
        graph = dict(self._graph)

        # Find all nodes with no incoming edges
        queue = deque([node for node in self._nodes if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Decrease in-degree for all neighbors
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycle
        if len(result) != len(self._nodes):
            remaining = self._nodes - set(result)
            raise DAGCycleError(
                f"Cycle detected in graph. Nodes involved: {remaining}"
            )

        return result

    def get_dependencies(self, node: Any) -> list[Any]:
        """
        Get all nodes that the given node depends on.

        Args:
            node: Node to find dependencies for

        Returns:
            List of dependency nodes
        """
        dependencies = []
        for from_node, to_nodes in self._graph.items():
            if node in to_nodes:
                dependencies.append(from_node)
        return dependencies

    def get_dependents(self, node: Any) -> list[Any]:
        """
        Get all nodes that depend on the given node.

        Args:
            node: Node to find dependents for

        Returns:
            List of dependent nodes
        """
        return list(self._graph.get(node, []))

    def get_execution_levels(self) -> list[list[Any]]:
        """
        Get nodes grouped by execution level.

        Nodes at the same level can be executed in parallel.

        Returns:
            List of levels, each containing nodes that can run in parallel

        Raises:
            DAGCycleError: If a cycle is detected in the graph
        """
        if not self._nodes:
            return []

        # Create working copies
        in_degree = dict(self._in_degree)
        graph = dict(self._graph)

        levels = []
        remaining_nodes = set(self._nodes)

        while remaining_nodes:
            # Find all nodes with no remaining dependencies
            level = [
                node for node in remaining_nodes
                if in_degree[node] == 0
            ]

            if not level:
                raise DAGCycleError(
                    f"Cycle detected. Remaining nodes: {remaining_nodes}"
                )

            levels.append(level)

            # Remove current level nodes and update in-degrees
            for node in level:
                remaining_nodes.remove(node)
                for neighbor in graph.get(node, []):
                    in_degree[neighbor] -= 1

        return levels

    def get_critical_path(self) -> list[Any]:
        """
        Get the critical path (longest path) through the graph.

        Returns:
            List of nodes on the critical path
        """
        if not self._nodes:
            return []

        # Calculate longest distance from each node
        sorted_nodes = self.topological_sort()
        distances: dict[Any, int] = {node: 0 for node in self._nodes}
        predecessors: dict[Any, Any] = {node: None for node in self._nodes}

        for node in sorted_nodes:
            for neighbor in self._graph.get(node, []):
                if distances[neighbor] < distances[node] + 1:
                    distances[neighbor] = distances[node] + 1
                    predecessors[neighbor] = node

        # Find the node with maximum distance
        end_node = max(distances.keys(), key=lambda n: distances[n])

        # Reconstruct path
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessors[current]

        return list(reversed(path))

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the DAG structure.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check for cycles
        try:
            self.topological_sort()
        except DAGCycleError as e:
            errors.append(str(e))

        # Check for orphan nodes (no dependencies and no dependents)
        for node in self._nodes:
            has_deps = self._in_degree[node] > 0
            has_dependents = bool(self._graph.get(node, []))

            if not has_deps and not has_dependents and len(self._nodes) > 1:
                errors.append(f"Orphan node detected: {node}")

        # Check for missing nodes in edges
        for from_node, to_nodes in self._graph.items():
            for to_node in to_nodes:
                if to_node not in self._nodes:
                    errors.append(
                        f"Edge references non-existent node: {from_node} -> {to_node}"
                    )

        return len(errors) == 0, errors

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._graph.clear()
        self._in_degree.clear()
        self._nodes.clear()

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    def __repr__(self) -> str:
        """Return string representation of the graph."""
        return f"DAGResolver(nodes={len(self._nodes)}, edges={sum(len(e) for e in self._graph.values())})"


def build_dag_from_tasks(tasks: list) -> DAGResolver:
    """
    Build a DAG from a list of tasks.

    Args:
        tasks: List of task objects with id and depends_on attributes

    Returns:
        DAGResolver: Configured DAG resolver
    """
    resolver = DAGResolver()

    # Add all tasks as nodes
    for task in tasks:
        resolver.add_node(task.id)

    # Add edges for dependencies
    for task in tasks:
        for dep_id in (task.depends_on or []):
            resolver.add_edge(dep_id, task.id)

    return resolver


def visualize_dag(resolver: DAGResolver) -> str:
    """
    Create a simple text visualization of the DAG.

    Args:
        resolver: DAG resolver instance

    Returns:
        Text representation of the DAG
    """
    try:
        levels = resolver.get_execution_levels()
    except DAGCycleError:
        return "Cannot visualize: Graph contains cycles"

    lines = ["DAG Visualization:", "=" * 40]

    for i, level in enumerate(levels):
        lines.append(f"Level {i}: {' -> '.join(str(n) for n in level)}")

    lines.append("=" * 40)
    lines.append(f"Critical Path: {' -> '.join(str(n) for n in resolver.get_critical_path())}")

    return "\n".join(lines)
