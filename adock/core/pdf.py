import os
import subprocess
import tempfile
import logging

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def pdf_response(response, pdf_filename):
    dest_dir = os.path.join(settings.MEDIA_ROOT, "tmp")
    if not os.access(dest_dir, os.W_OK):
        logger.info("Unable to write in %s, trying to create it...", dest_dir)
        os.mkdir(dest_dir)

    (_, html_filename) = tempfile.mkstemp(
        prefix=pdf_filename.replace(".pdf", ""), suffix=".html", dir=dest_dir
    )
    with open(html_filename, "w+") as f:
        content = response.content.decode()
        content = content.replace(
            'href="%s' % settings.STATIC_URL, 'href="%s/' % settings.STATIC_ROOT
        )
        content = content.replace(
            'src="%s' % settings.MEDIA_URL, 'src="%s/' % settings.MEDIA_ROOT
        )
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
    return response
