"""
Load Balancer Service - Request Distribution Logic

This service provides load balancing logic for distributing requests
across multiple backend workers using various algorithms.
"""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional
from enum import Enum
from collections import defaultdict

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class LoadBalancingAlgorithm(str, Enum):
    """Supported load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class BackendServer:
    """Represents a backend server for load balancing."""

    def __init__(
        self,
        server_id: str,
        host: str,
        port: int,
        weight: int = 1,
        max_connections: int = 100
    ):
        self.server_id = server_id
        self.host = host
        self.port = port
        self.weight = weight
        self.max_connections = max_connections
        self.current_connections = 0
        self.total_requests = 0
        self.total_response_time = 0.0
        self.failed_requests = 0
        self.is_healthy = True
        self.last_health_check = time.time()

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def avg_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server_id": self.server_id,
            "host": self.host,
            "port": self.port,
            "weight": self.weight,
            "max_connections": self.max_connections,
            "current_connections": self.current_connections,
            "total_requests": self.total_requests,
            "avg_response_time": self.avg_response_time,
            "failed_requests": self.failed_requests,
            "is_healthy": self.is_healthy,
            "last_health_check": self.last_health_check
        }


class LoadBalancer:
    """
    Load balancer for distributing requests across backend servers.
    """

    def __init__(self, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN):
        self.algorithm = algorithm
        self._servers: Dict[str, BackendServer] = {}
        self._round_robin_index = 0
        self._weighted_index = 0
        self._weighted_servers: List[str] = []
        self._lock = asyncio.Lock()

    async def add_server(
        self,
        server_id: str,
        host: str,
        port: int,
        weight: int = 1,
        max_connections: int = 100
    ) -> None:
        """Add a backend server to the pool."""
        async with self._lock:
            server = BackendServer(
                server_id=server_id,
                host=host,
                port=port,
                weight=weight,
                max_connections=max_connections
            )
            self._servers[server_id] = server
            self._rebuild_weighted_list()

            logger.info(
                "Backend server added",
                server_id=server_id,
                address=server.address,
                weight=weight
            )

    async def remove_server(self, server_id: str) -> bool:
        """Remove a backend server from the pool."""
        async with self._lock:
            if server_id in self._servers:
                del self._servers[server_id]
                self._rebuild_weighted_list()
                logger.info("Backend server removed", server_id=server_id)
                return True
            return False

    async def update_server(
        self,
        server_id: str,
        weight: Optional[int] = None,
        max_connections: Optional[int] = None,
        is_healthy: Optional[bool] = None
    ) -> bool:
        """Update server properties."""
        async with self._lock:
            if server_id not in self._servers:
                return False

            server = self._servers[server_id]

            if weight is not None:
                server.weight = weight
                self._rebuild_weighted_list()
            if max_connections is not None:
                server.max_connections = max_connections
            if is_healthy is not None:
                server.is_healthy = is_healthy
                server.last_health_check = time.time()

            return True

    def _rebuild_weighted_list(self) -> None:
        """Rebuild the weighted server list for weighted round robin."""
        self._weighted_servers = []
        for server_id, server in self._servers.items():
            if server.is_healthy:
                self._weighted_servers.extend([server_id] * server.weight)

    async def get_server(self, client_ip: Optional[str] = None) -> Optional[BackendServer]:
        """
        Get the next server based on the configured algorithm.

        Args:
            client_ip: Client IP for IP hash algorithm

        Returns:
            Selected backend server or None if no servers available
        """
        async with self._lock:
            healthy_servers = [s for s in self._servers.values() if s.is_healthy]

            if not healthy_servers:
                logger.warning("No healthy servers available")
                return None

            if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                server = await self._round_robin(healthy_servers)
            elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                server = await self._least_connections(healthy_servers)
            elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                server = await self._weighted_round_robin()
            elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
                server = random.choice(healthy_servers)
            elif self.algorithm == LoadBalancingAlgorithm.IP_HASH:
                server = await self._ip_hash(healthy_servers, client_ip)
            elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
                server = await self._least_response_time(healthy_servers)
            else:
                server = await self._round_robin(healthy_servers)

            if server:
                server.current_connections += 1
                server.total_requests += 1

            return server

    async def _round_robin(self, servers: List[BackendServer]) -> BackendServer:
        """Round robin selection."""
        server = servers[self._round_robin_index % len(servers)]
        self._round_robin_index += 1
        return server

    async def _least_connections(self, servers: List[BackendServer]) -> BackendServer:
        """Select server with least active connections."""
        return min(servers, key=lambda s: s.current_connections)

    async def _weighted_round_robin(self) -> Optional[BackendServer]:
        """Weighted round robin selection."""
        if not self._weighted_servers:
            return None

        server_id = self._weighted_servers[self._weighted_index % len(self._weighted_servers)]
        self._weighted_index += 1
        return self._servers.get(server_id)

    async def _ip_hash(
        self,
        servers: List[BackendServer],
        client_ip: Optional[str]
    ) -> BackendServer:
        """IP hash selection for session persistence."""
        if client_ip:
            hash_value = hash(client_ip)
            index = hash_value % len(servers)
            return servers[index]
        return await self._round_robin(servers)

    async def _least_response_time(self, servers: List[BackendServer]) -> BackendServer:
        """Select server with lowest average response time."""
        return min(servers, key=lambda s: s.avg_response_time)

    async def release_connection(
        self,
        server_id: str,
        response_time: float = 0.0,
        success: bool = True
    ) -> None:
        """
        Release a connection and update server statistics.

        Args:
            server_id: Server identifier
            response_time: Request response time in seconds
            success: Whether the request was successful
        """
        async with self._lock:
            if server_id in self._servers:
                server = self._servers[server_id]
                server.current_connections = max(0, server.current_connections - 1)
                server.total_response_time += response_time

                if not success:
                    server.failed_requests += 1

    async def get_all_servers(self) -> List[Dict[str, Any]]:
        """Get information about all servers."""
        return [server.to_dict() for server in self._servers.values()]

    async def get_server_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for all servers."""
        total_requests = sum(s.total_requests for s in self._servers.values())
        total_failed = sum(s.failed_requests for s in self._servers.values())
        total_connections = sum(s.current_connections for s in self._servers.values())
        healthy_count = sum(1 for s in self._servers.values() if s.is_healthy)

        return {
            "total_servers": len(self._servers),
            "healthy_servers": healthy_count,
            "unhealthy_servers": len(self._servers) - healthy_count,
            "total_requests": total_requests,
            "total_failed_requests": total_failed,
            "active_connections": total_connections,
            "algorithm": self.algorithm.value,
            "error_rate": (total_failed / total_requests * 100) if total_requests > 0 else 0.0
        }

    async def set_algorithm(self, algorithm: LoadBalancingAlgorithm) -> None:
        """Change the load balancing algorithm."""
        async with self._lock:
            self.algorithm = algorithm
            logger.info("Load balancing algorithm changed", algorithm=algorithm.value)

    async def reset_stats(self) -> None:
        """Reset all server statistics."""
        async with self._lock:
            for server in self._servers.values():
                server.total_requests = 0
                server.total_response_time = 0.0
                server.failed_requests = 0

            logger.info("Server statistics reset")
