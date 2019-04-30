import logging

from django.conf import settings
from django.core.mail import mail_managers
from django.http.response import JsonResponse
import sentry_sdk

from adock.core import views as core_views
from adock.accounts.decorators import user_is_staff
from adock.meta import models as meta_models

logger = logging.getLogger(__name__)


@user_is_staff()
def selftest_index(request):
    if request.method == "POST":
        payload, response = core_views.request_load(request)
        if response:
            return response
        if "add_log_entry" in payload:
            message = "An error entry has been added to the logs."
            logger.error(message)
            output = 'Logger called with "%s"' % message
        elif "mail_managers" in payload:
            subject = "Selftest mail"
            message = "Message sent by selftest page of {website}.".format(
                website=settings.HTTP_SERVER_URL
            )
            mail_managers(subject, message, fail_silently=False)
            output = "Mail sent to %s." % ", ".join(
                manager[0] for manager in settings.MANAGERS
            )
        elif "connect_db" in payload:
            metas = meta_models.Meta.objects.all()
            if metas:
                output = metas[0].data
            else:
                output = "No Meta entries in DB."
        elif "raise_exception" in payload:
            raise Exception("Raised by selftest page (safe to ignore).")
        elif "capture_event" in payload:
            event_id = sentry_sdk.capture_message("Event captured in selftest page.")
            output = "Event captured #%s" % event_id
        else:
            return JsonResponse(
                {"message": "Invalid action (%s)" % payload}, status=400
            )
        return JsonResponse({"output": output})
    else:
        return JsonResponse(
            {
                "actions": {
                    "add_log_entry": "Add entry to Django log",
                    "mail_managers": "Mail managers",
                    "connect_db": "Connect to DB",
                    "raise_exception": "Raise an exception (for Sentry)",
                    "capture_event": "Capture an event for Sentry",
                }
            }
        )
