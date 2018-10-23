import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_managers
from django.shortcuts import render

from sentry_sdk import capture_message

from ..meta import models as meta_models

logger = logging.getLogger(__name__)


@login_required
def selftest_index(request):
    """Render a page with various selftest actions and run each action on POST"""
    results = None
    if request.method == "POST":
        if "add_log_entry" in request.POST:
            message = "An error entry has been added to the logs."
            logger.error(message)
            results = 'Logger called with "%s"' % message
        elif "mail_managers" in request.POST:
            subject = "Selftest mail"
            message = "Message sent by selftest page of {website}.".format(
                website=settings.WEBSITE
            )
            mail_managers(subject, message, fail_silently=False)
            results = "Mail sent to %s." % ", ".join(
                manager[0] for manager in settings.MANAGERS
            )
        elif "connect_db" in request.POST:
            metas = meta_models.Meta.objects.all()
            if metas:
                results = metas[0].data
            else:
                results = "No Meta entries in DB."
        elif "raise_exception" in request.POST:
            raise Exception("Raised by selftest page (safe to ignore).")
        elif "capture_event" in request.POST:
            event_id = capture_message("Event captured in selftest page.")
            results = "Event captured #%s" % event_id

    return render(request, "selftest.html", {"results": results})
