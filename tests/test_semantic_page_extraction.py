from backend.app.services.extraction_engine import build_extraction_plan
from backend.app.services.extraction_executor import execute_extraction


def test_semantic_page_heading_and_first_paragraph_extraction():
    html = """
    <html>
        <head>
            <title>Example Domain</title>
        </head>
        <body>
            <h1>Example Domain</h1>
            <p>This is the first paragraph.</p>
            <p>This is the second paragraph.</p>
        </body>
    </html>
    """

    plan = build_extraction_plan(
        "Extract the page heading as title and the first paragraph as description"
    )

    result = execute_extraction(
        html,
        plan,
        "https://example.com",
    )

    assert result.records
    assert result.records[0]["title"] == "Example Domain"
    assert result.records[0]["description"] == "This is the first paragraph."
