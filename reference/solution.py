#!/usr/bin/env python3
"""Enterprise Contact Center - Capstone Project.

Lab 3.6 Deliverable: Multi-agent system with gateway routing,
orders management, and support handling.
"""

import os
from datetime import datetime
from signalwire_agents import AgentBase, AgentServer, SwaigFunctionResult


# ============================================================
# Gateway Agent - Routes calls to appropriate department
# ============================================================

class GatewayAgent(AgentBase):
    """Gateway agent that routes callers to the right department."""

    DEPARTMENTS = {
        "orders": {"route": "/orders", "description": "Order status and tracking"},
        "support": {"route": "/support", "description": "Technical support"},
        "billing": {"route": "/billing", "description": "Billing inquiries"}
    }

    def __init__(self):
        super().__init__(name="gateway-agent", route="/gateway")

        self.prompt_add_section(
            "Role",
            "You are the main gateway for our contact center. "
            "Determine what the caller needs and route them appropriately."
        )

        self.prompt_add_section(
            "Available Departments",
            bullets=[
                "Orders - for order status, tracking, returns",
                "Support - for technical issues and troubleshooting",
                "Billing - for payment and invoice questions"
            ]
        )

        self.prompt_add_section(
            "Instructions",
            bullets=[
                "Greet the caller warmly",
                "Ask how you can help",
                "Route to the appropriate department",
                "If unclear, ask clarifying questions"
            ]
        )

        self.add_language("English", "en-US", "rime.spore")
        self._setup_functions()

    def _setup_functions(self):
        @self.tool(
            description="Route call to the appropriate department",
            parameters={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "enum": ["orders", "support", "billing"],
                        "description": "Department to route to"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the transfer"
                    }
                },
                "required": ["department"]
            }
        )
        def route_call(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            department = args.get("department", "").lower()
            reason = args.get("reason", "customer request")

            dept_info = self.DEPARTMENTS.get(department)
            if not dept_info:
                return SwaigFunctionResult(
                    "I'm not sure which department can help with that. "
                    "Could you tell me more about what you need?"
                )

            return (
                SwaigFunctionResult(
                    f"I'll transfer you to our {department} team now.",
                    post_process=True
                )
                .swml_transfer(dept_info["route"], "Goodbye!", final=True)
            )


# ============================================================
# Orders Agent - Handles order inquiries
# ============================================================

class OrdersAgent(AgentBase):
    """Orders agent for order status and management."""

    # Simulated order database
    ORDERS = {
        "ORD-001": {"status": "shipped", "tracking": "1Z999AA10123456784", "items": ["Widget Pro"]},
        "ORD-002": {"status": "processing", "tracking": None, "items": ["Gadget Plus", "Cable"]},
        "ORD-003": {"status": "delivered", "tracking": "1Z999AA10123456785", "items": ["Super Device"]}
    }

    def __init__(self):
        super().__init__(name="orders-agent", route="/orders")

        self.prompt_add_section(
            "Role",
            "You are an orders specialist. Help customers with order status, "
            "tracking, and returns."
        )

        self.prompt_add_section(
            "Instructions",
            bullets=[
                "Ask for order number if not provided",
                "Provide clear status updates",
                "Offer to help with returns if needed",
                "Transfer to support for technical issues"
            ]
        )

        self.add_language("English", "en-US", "rime.spore")
        self._setup_functions()

    def _setup_functions(self):
        @self.tool(
            description="Look up order status",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to look up"
                    }
                },
                "required": ["order_id"]
            },
            fillers=["Let me look that up..."]
        )
        def get_order_status(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            order_id = args.get("order_id", "").upper()

            order = self.ORDERS.get(order_id)
            if not order:
                return SwaigFunctionResult(
                    f"I couldn't find order {order_id}. "
                    "Please verify the order number and try again."
                )

            status = order["status"]
            tracking = order.get("tracking")
            items = ", ".join(order["items"])

            response = f"Order {order_id} containing {items} is {status}."
            if tracking:
                response += f" Tracking number: {tracking}."

            return SwaigFunctionResult(response)

        @self.tool(
            description="Initiate a return",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to return"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for return"
                    }
                },
                "required": ["order_id", "reason"]
            }
        )
        def initiate_return(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            order_id = args.get("order_id", "").upper()
            reason = args.get("reason", "")

            order = self.ORDERS.get(order_id)
            if not order:
                return SwaigFunctionResult(
                    f"I couldn't find order {order_id}. "
                    "Please verify the order number."
                )

            return_id = f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return SwaigFunctionResult(
                f"Return initiated for order {order_id}. "
                f"Your return ID is {return_id}. "
                "You'll receive an email with return instructions."
            )

        @self.tool(
            description="Transfer to support for technical issues",
            parameters={
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue"
                    }
                },
                "required": ["issue"]
            }
        )
        def transfer_to_support(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            return (
                SwaigFunctionResult(
                    "I'll transfer you to our support team for technical assistance.",
                    post_process=True
                )
                .swml_transfer("/support", "Goodbye!", final=True)
            )


# ============================================================
# Support Agent - Handles technical support
# ============================================================

class SupportAgent(AgentBase):
    """Support agent for technical issues."""

    def __init__(self):
        super().__init__(name="support-agent", route="/support")

        self.prompt_add_section(
            "Role",
            "You are a technical support specialist. Help customers troubleshoot "
            "issues and resolve problems."
        )

        self.prompt_add_section(
            "Instructions",
            bullets=[
                "Listen carefully to the issue",
                "Ask clarifying questions",
                "Provide step-by-step troubleshooting",
                "Create tickets for complex issues",
                "Escalate when needed"
            ]
        )

        self.add_language("English", "en-US", "rime.spore")
        self._setup_functions()

    def _setup_functions(self):
        @self.tool(
            description="Troubleshoot a technical issue",
            parameters={
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product having issues"
                    }
                },
                "required": ["issue"]
            },
            fillers=["Let me look into that..."]
        )
        def troubleshoot(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            issue = args.get("issue", "").lower()
            product = args.get("product", "your product")

            # Common troubleshooting responses
            if any(word in issue for word in ["won't turn on", "power", "start"]):
                return SwaigFunctionResult(
                    f"For {product} power issues, try: "
                    "1) Check the power connection, "
                    "2) Try a different outlet, "
                    "3) Hold the power button for 10 seconds. "
                    "Did any of these help?"
                )

            if any(word in issue for word in ["connect", "wifi", "network", "internet"]):
                return SwaigFunctionResult(
                    "For connectivity issues: "
                    "1) Restart your router, "
                    "2) Forget and reconnect to the network, "
                    "3) Check for firmware updates. "
                    "Would you like more detailed steps?"
                )

            if any(word in issue for word in ["slow", "performance", "lag"]):
                return SwaigFunctionResult(
                    "For performance issues: "
                    "1) Close unused applications, "
                    "2) Clear cache and temporary files, "
                    "3) Restart the device. "
                    "Should I create a ticket for further investigation?"
                )

            return SwaigFunctionResult(
                "I'll help troubleshoot that issue. "
                "Can you provide more details about what's happening?"
            )

        @self.tool(
            description="Create a support ticket",
            parameters={
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Issue description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Ticket priority"
                    }
                },
                "required": ["issue"]
            }
        )
        def create_ticket(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            issue = args.get("issue", "")
            priority = args.get("priority", "medium")

            ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return (
                SwaigFunctionResult(
                    f"Created support ticket {ticket_id} with {priority} priority. "
                    "Our team will follow up within 24 hours."
                )
                .update_global_data({
                    "ticket_id": ticket_id,
                    "ticket_priority": priority
                })
            )

        @self.tool(
            description="Transfer back to gateway for other needs",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for transfer"
                    }
                }
            }
        )
        def transfer_to_gateway(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            return (
                SwaigFunctionResult(
                    "I'll transfer you back to our main line.",
                    post_process=True
                )
                .swml_transfer("/gateway", "Goodbye!", final=True)
            )


# ============================================================
# Server Setup
# ============================================================

def create_server():
    """Create multi-agent server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))

    server = AgentServer(host=host, port=port)

    # Register all agents
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

    return server


if __name__ == "__main__":
    server = create_server()
    server.run()
