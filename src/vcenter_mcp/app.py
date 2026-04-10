"""Shared FastMCP application instance."""

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP(
    "vcenter-mcp",
    instructions=(
        "Provides safe read-only access to Broadcom VCF and VMware vCenter Server "
        "Appliance REST APIs. Start with list_vcenters or get_vcenter_inventory to "
        "discover configured endpoints. Pass vcenter_name when more than one vCenter "
        "is configured. Tools only call documented read-only API operations."
    ),
)
