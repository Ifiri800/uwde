from backend.app.services.api.errors import APIResponseError
from backend.app.services.api.models import APIResponse
from backend.app.services.api.parser import parse_api_response


def make_response(
    body: bytes,
    content_type: str,
) -> APIResponse:
    return APIResponse(
        url="https://api.example.com/data",
        final_url="https://api.example.com/data",
        status_code=200,
        content_type=content_type,
        headers={
            "content-type": content_type,
        },
        body=body,
    )


def test_parse_json_object():
    response = make_response(
        b'{"name":"UWDE","version":"1.0"}',
        "application/json",
    )

    result = parse_api_response(response)

    assert result == {
        "name": "UWDE",
        "version": "1.0",
    }


def test_parse_json_array():
    response = make_response(
        b'[{"id":1},{"id":2}]',
        "application/json",
    )

    result = parse_api_response(response)

    assert result == [
        {"id": 1},
        {"id": 2},
    ]


def test_parse_nested_json():
    response = make_response(
        (
            b'{"data":{"companies":'
            b'[{"name":"A"},{"name":"B"}]}}'
        ),
        "application/json; charset=utf-8",
    )

    result = parse_api_response(response)

    assert result["data"]["companies"][0]["name"] == "A"
    assert result["data"]["companies"][1]["name"] == "B"


def test_parse_vendor_json_content_type():
    response = make_response(
        b'{"status":"ok"}',
        "application/vnd.api+json",
    )

    result = parse_api_response(response)

    assert result == {"status": "ok"}


def test_parse_xml():
    response = make_response(
        (
            b"<response>"
            b"<name>UWDE</name>"
            b"<status>ok</status>"
            b"</response>"
        ),
        "application/xml",
    )

    result = parse_api_response(response)

    assert result == {
        "response": {
            "name": "UWDE",
            "status": "ok",
        }
    }


def test_parse_xml_repeated_elements():
    response = make_response(
        (
            b"<companies>"
            b"<company>A</company>"
            b"<company>B</company>"
            b"</companies>"
        ),
        "text/xml",
    )

    result = parse_api_response(response)

    assert result == {
        "companies": {
            "company": [
                "A",
                "B",
            ]
        }
    }


def test_parse_plain_text():
    response = make_response(
        b"hello from api",
        "text/plain",
    )

    result = parse_api_response(response)

    assert result == "hello from api"


def test_parse_json_from_plain_text():
    response = make_response(
        b'{"message":"ok"}',
        "text/plain",
    )

    result = parse_api_response(response)

    assert result == {
        "message": "ok",
    }


def test_parse_empty_response():
    response = make_response(
        b"",
        "application/json",
    )

    result = parse_api_response(response)

    assert result is None


def test_reject_invalid_json():
    response = make_response(
        b'{"broken":',
        "application/json",
    )

    try:
        parse_api_response(response)
    except APIResponseError as exc:
        assert "invalid JSON" in str(exc)
    else:
        raise AssertionError(
            "Expected APIResponseError"
        )


def test_reject_invalid_xml():
    response = make_response(
        b"<broken>",
        "application/xml",
    )

    try:
        parse_api_response(response)
    except APIResponseError as exc:
        assert "invalid XML" in str(exc)
    else:
        raise AssertionError(
            "Expected APIResponseError"
        )


def test_reject_unsupported_content_type():
    response = make_response(
        b"binary data",
        "application/octet-stream",
    )

    try:
        parse_api_response(response)
    except APIResponseError as exc:
        assert "Unsupported API response content type" in str(exc)
    else:
        raise AssertionError(
            "Expected APIResponseError"
        )
