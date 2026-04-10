"""Read-only tagging tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.client import vcenter_get, vcenter_post_readonly
from vcenter_mcp.registry import json_response, resolve_vcenter


@mcp.tool()
def list_tag_categories(vcenter_name: str | None = None) -> str:
    """List all tag category identifiers."""
    return json_response(vcenter_get("/api/cis/tagging/category", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_tags(vcenter_name: str | None = None) -> str:
    """List all tag identifiers."""
    return json_response(vcenter_get("/api/cis/tagging/tag", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_attached_tags(object_type: str, object_id: str, vcenter_name: str | None = None) -> str:
    """List tags attached to a specific vCenter object."""
    body = {"object_id": {"type": object_type, "id": object_id}}
    return json_response(
        vcenter_post_readonly(
            "/api/cis/tagging/tag-association?action=list-attached-tags",
            json_body=body,
            **resolve_vcenter(vcenter_name),
        )
    )


@mcp.tool()
def list_used_tag_categories(used_by_entity: str, vcenter_name: str | None = None) -> str:
    """List tag categories used by a subscriber entity."""
    body = {"used_by_entity": used_by_entity}
    return json_response(
        vcenter_post_readonly(
            "/api/cis/tagging/category?action=list-used-categories",
            json_body=body,
            **resolve_vcenter(vcenter_name),
        )
    )
