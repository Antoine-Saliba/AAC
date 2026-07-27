def test_preflight_request_allows_browser_requests(client):
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in {"*", "http://127.0.0.1:5500"}
