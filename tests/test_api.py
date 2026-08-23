from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "uwde-api"


def test_analyze_requires_instruction():
    response = client.post(
        "/api/analyze",
        json={
            "url": "https://example.com",
        },
    )

    assert response.status_code == 422


def test_analyze_rejects_invalid_url():
    response = client.post(
        "/api/analyze",
        json={
            "url": "not-a-url",
            "instruction": "Extract the title",
        },
    )

    assert response.status_code == 422


def test_analyze_accepts_valid_request(monkeypatch):
    class FakeAnalysis:
        url = "https://example.com"
        final_url = "https://example.com/"
        status_code = 200
        content_type = "text/html"
        title = "Example Domain"
        headings = ["Example"]
        paragraphs_count = 1
        links_count = 1
        images_count = 0
        lists_count = 0
        tables_count = 0

    def fake_analyze(url):
        assert url == "https://example.com/"
        return FakeAnalysis()

    monkeypatch.setattr(
        "backend.app.main.analyze_website",
        fake_analyze,
    )

    response = client.post(
        "/api/analyze",
        json={
            "url": "https://example.com",
            "instruction": "Extract the page title",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["title"] == "Example Domain"
    assert data["instruction"] == "Extract the page title"
    assert data["links_count"] == 1

def test_extract_returns_structured_records(monkeypatch):
    class FakeFetchResult:
        url = "https://example.com"
        final_url = "https://example.com/"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <article>
                    <h2>Example Job</h2>
                    <div class="company">Example Company</div>
                    <div class="location">Lagos</div>
                </article>
            </body>
        </html>
        """

    def fake_fetch(url):
        assert url == "https://example.com/"
        return FakeFetchResult()

    monkeypatch.setattr(
        "backend.app.main.fetch_url",
        fake_fetch,
    )

    response = client.post(
        "/api/extract",
        json={
            "url": "https://example.com",
            "instruction": "Extract title, company and location",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert "records" in data
    assert len(data["records"]) == 1    