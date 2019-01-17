import os
import subprocess
import tempfile
import logging

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def pdf_response(response, pdf_filename):
    (_, html_filename) = tempfile.mkstemp(
        prefix=pdf_filename.replace(".pdf", ""), suffix=".html"
    )
    with open(html_filename, "w+") as f:
        content = response.content.decode()
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
