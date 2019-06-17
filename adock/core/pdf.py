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


def pdf_response(html_content, pdf_filename):
    (temp_html_fd, temp_html_path) = tempfile.mkstemp(
        prefix=pdf_filename.replace(".pdf", ""), suffix=".html", text=True
    )
    with open(temp_html_path, "w") as f:
        f.write(html_content)

    (temp_pdf_fd, temp_pdf_path) = tempfile.mkstemp(
        prefix=pdf_filename.replace(".pdf", ""), suffix=".pdf"
    )
    ps = subprocess.Popen(
        [
            "node",
            os.path.join(settings.BASE_DIR, "htmltopdf.js"),
            temp_html_path,
            temp_pdf_path,
        ]
    )
    ps.wait()

    os.close(temp_html_fd)
    os.remove(temp_html_path)

    with open(temp_pdf_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="%s"' % (pdf_filename)

    os.close(temp_pdf_fd)
    os.remove(temp_pdf_path)

    return response
