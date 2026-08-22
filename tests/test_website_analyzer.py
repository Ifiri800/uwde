import httpx

from backend.app.services.website_analyzer import analyze_website


HTML = """
<!doctype html>
<html>
<head>
    <title>UWDE Test Site</title>
</head>
<body>
    <h1>Job Opportunities</h1>
    <h2>Engineering</h2>

    <p>Find your next job.</p>
    <p>Apply today.</p>

    <a href="/jobs/1">Developer</a>
    <a href="/jobs/2">Designer</a>

    <img src="/logo.png" alt="Logo">

    <ul>
        <li>Python</li>
        <li>FastAPI</li>
    </ul>

    <table>
        <tr>
            <th>Job</th>
            <th>Location</th>
        </tr>
        <tr>
            <td>Developer</td>
            <td>Lagos</td>
        </tr>
    </table>
</body>
</html>
"""


def test_analyze_website(monkeypatch):
    response = httpx.Response(
        200,
        headers={
            "content-type": "text/html; charset=utf-8",
        },
        content=HTML.encode(),
        request=httpx.Request(
            "GET",
            "https://example.com/jobs",
        ),
    )

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    result = analyze_website("https://example.com/jobs")

    assert result.url == "https://example.com/jobs"
    assert result.final_url == "https://example.com/jobs"
    assert result.status_code == 200
    assert result.title == "UWDE Test Site"

    assert result.headings == [
        "Job Opportunities",
        "Engineering",
    ]

    assert result.paragraphs_count == 2
    assert result.links_count == 2
    assert result.images_count == 1
    assert result.lists_count == 1
    assert result.tables_count == 1


def test_analysis_can_be_serialized(monkeypatch):
    response = httpx.Response(
        200,
        headers={
            "content-type": "text/html",
        },
        content=b"""
        <html>
            <head>
                <title>Test</title>
            </head>
            <body>
                <h1>Hello</h1>
            </body>
        </html>
        """,
        request=httpx.Request(
            "GET",
            "https://example.com",
        ),
    )

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    result = analyze_website("https://example.com")

    data = result.to_dict()

    assert data["url"] == "https://example.com"
    assert data["title"] == "Test"
    assert data["headings"] == ["Hello"]
    assert data["links_count"] == 0


def test_analyzer_propagates_fetch_errors():
    from backend.app.services.website_analyzer import analyze_website
    from backend.app.services.http_fetcher import FetchError

    try:
        analyze_website("http://127.0.0.1")
    except FetchError:
        pass
    else:
        raise AssertionError(
            "Expected unsafe URL to raise FetchError"
        )