"""
Dependency resolver - topological sort for agent dependencies.
"""
from typing import Dict, List
from collections import defaultdict, deque


class DependencyResolver:
    """Resolves agent dependencies using topological sort."""

    def resolve(
        self,
        agents: List[str],
        dependencies: Dict[str, List[str]],
    ) -> List[List[str]]:
        """
        Resolve execution order based on dependencies.
        Returns list of batches that can be executed in parallel.

        Args:
            agents: List of agent IDs
            dependencies: Map of agent -> list of dependencies

        Returns:
            List of batches (each batch can run in parallel)
        """
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = {agent: 0 for agent in agents}

        for agent in agents:
            for dep in dependencies.get(agent, []):
                if dep in agents:
                    graph[dep].append(agent)
                    in_degree[agent] += 1

        # Kahn's algorithm for topological sort with level grouping
        batches = []
        queue = deque([a for a in agents if in_degree[a] == 0])

        while queue:
            batch = []
            for _ in range(len(queue)):
                agent = queue.popleft()
                batch.append(agent)

                for dependent in graph[agent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

            if batch:
                batches.append(batch)

        # Check for cycles
        total_sorted = sum(len(b) for b in batches)
        if total_sorted != len(agents):
            raise ValueError("Circular dependency detected in agents")

        return batches
