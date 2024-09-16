from src.entrypoint.server import Token


def test_token_methods() -> None:
    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiJpZCIsInVzZXJuYW1lIjoiaW50aXMifQ"
        ".v_OS-IiM7_P4Oe3Z2oROIGA1zvoIasmRbd7UebVBmMI"
    )

    t = Token.from_encoded(token)
    assert t.sub == "id"
    assert t.username == "intis"
    assert t.produce() == token
