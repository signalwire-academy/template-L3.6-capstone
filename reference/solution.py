#!/usr/bin/env python3
"""Main entry point for enterprise contact center.

Capstone Deliverable: Multi-agent server setup.
"""

import os
from datetime import datetime
from signalwire_agents import AgentServer

from agents.gateway_agent import GatewayAgent
from agents.orders_agent import OrdersAgent
from agents.support_agent import SupportAgent
from shared.logging_config import get_logger
from shared.metrics import start_metrics_server

logger = get_logger("main")


def create_server():
    """Create multi-agent server with health endpoints."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    metrics_port = int(os.getenv("METRICS_PORT", "9090"))

    logger.info(f"Starting server on {host}:{port}")

    # Start metrics server
    if start_metrics_server(metrics_port):
        logger.info(f"Metrics server on port {metrics_port}")

    # Create server and register agents
    server = AgentServer(host=host, port=port)
    server.register(GatewayAgent())
    server.register(OrdersAgent())
    server.register(SupportAgent())

    # Health endpoint
    @server.app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": ["gateway", "orders", "support"],
            "version": os.getenv("APP_VERSION", "1.0.0")
        }

    @server.app.get("/ready")
    async def ready():
        return {"ready": True}

    logger.info("All agents registered")
    return server


if __name__ == "__main__":
    server = create_server()
    server.run()
