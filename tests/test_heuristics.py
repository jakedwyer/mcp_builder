from mcp_builder.orchestration.llm import HeuristicLLMClient, extract_endpoints


def test_extract_endpoints_basic():
    text = """
    The API exposes GET /users and POST /users endpoints. Use DELETE /users/{id} to remove.
    """
    endpoints = extract_endpoints(text)
    paths = {ep.path for ep in endpoints}
    assert "/users" in paths
    assert "/users/{id}" in paths


def test_heuristic_llm_generates_blueprint():
    client = HeuristicLLMClient()
    blueprint = client.generate_blueprint("GET /items")
    assert blueprint.endpoints
    assert blueprint.endpoints[0].path == "/items"
