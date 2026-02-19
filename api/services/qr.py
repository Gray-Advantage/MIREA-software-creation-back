import base64
import io
import uuid

import qrcode


def generate_qr_image(token: uuid.UUID, base_url: str = "") -> str:
    scan_url = f"{base_url}/api/qr/scan?token={token}"
    img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")
