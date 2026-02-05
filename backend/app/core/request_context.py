from fastapi import Header


def get_request_context(
    x_tenant_id: str = Header(default="default"),
    x_region: str = Header(default="in"),
):
    """
    Provides tenant & region context for each request.
    """
    return {
        "tenant_id": x_tenant_id,
        "region": x_region,
    }
