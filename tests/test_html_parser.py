from backend.app.services.html_parser import parse_html


HTML = """
<!doctype html>
<html>
<head>
    <title>Example Jobs</title>
</head>
<body>
    <h1>Available Jobs</h1>
    <h2>Engineering</h2>

    <p>Find your next opportunity.</p>

    <a href="/jobs/1">Senior Developer</a>
    <a href="https://example.org/about">About</a>

    <img src="/images/logo.png" alt="Company Logo">

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


def test_extracts_title():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.title == "Example Jobs"


def test_extracts_headings():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.headings == [
        "Available Jobs",
        "Engineering",
    ]


def test_extracts_paragraphs():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.paragraphs == [
        "Find your next opportunity.",
    ]


def test_resolves_relative_links():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.links[0].url == "https://example.com/jobs/1"
    assert page.links[0].text == "Senior Developer"

    assert page.links[1].url == "https://example.org/about"


def test_extracts_images():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.images[0].alt == "Company Logo"
    assert page.images[0].url == "https://example.com/images/logo.png"


def test_extracts_lists():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.lists == [
        [
            "Python",
            "FastAPI",
        ]
    ]


def test_extracts_tables():
    page = parse_html(HTML, "https://example.com/jobs")

    assert page.tables == [
        [
            ["Job", "Location"],
            ["Developer", "Lagos"],
        ]
    ]


def test_handles_missing_title():
    html = "<html><body><h1>Hello</h1></body></html>"

    page = parse_html(html, "https://example.com")

    assert page.title == ""
    assert page.headings == ["Hello"]


def test_normalizes_whitespace():
    html = """
    <html>
        <head>
            <title>
                Example    Website
            </title>
        </head>
        <body>
            <p>
                Hello
                world
            </p>
        </body>
    </html>
    """

    page = parse_html(html, "https://example.com")

    assert page.title == "Example Website"
    assert page.paragraphs == ["Hello world"]