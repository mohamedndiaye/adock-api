import io
import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.http import HttpResponse
import qrcode
import qrcode.image.svg

logger = logging.getLogger(__name__)


def get_qr_code(data=None, border=2, box_size=7):
    qr = qrcode.QRCode(
        image_factory=qrcode.image.svg.SvgImage, border=border, box_size=box_size
    )
    qr.add_data(data)
    svg = qr.make_image()
    svg_content = io.BytesIO()
    svg.save(svg_content)
    content = svg_content.getvalue().decode("utf-8")
    return content


def pdf_response(response, pdf_filename):
    (_, html_filename) = tempfile.mkstemp(
        prefix=pdf_filename.replace(".pdf", ""), suffix=".html"
    )
    with open(html_filename, "w+") as f:
        content = response.content.decode("utf-8")
        f.write(content)

    ps = subprocess.Popen(
        [
            "node",
            os.path.join(settings.BASE_DIR, "htmltopdf.js"),
            html_filename,
            pdf_filename,
        ]
    )
    ps.wait()

    os.remove(html_filename)

    with open(pdf_filename, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="%s"' % (pdf_filename)

    os.remove(pdf_filename)
    return response
