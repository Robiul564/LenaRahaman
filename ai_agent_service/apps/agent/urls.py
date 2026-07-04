from django.urls import path

from apps.agent.views import ProcessMessageView

urlpatterns = [
    path("process-message/", ProcessMessageView.as_view(), name="process-message"),
]
