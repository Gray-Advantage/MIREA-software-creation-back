import uuid

from api.services.qr import generate_qr_image


def test_generate_qr_image_returns_base64_png() -> None:
    token = uuid.uuid4()
    b64 = generate_qr_image(token, base_url="http://localhost:8001")
    assert isinstance(b64, str)
    assert len(b64) > 100  # noqa: PLR2004
