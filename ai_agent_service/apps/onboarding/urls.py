from django.urls import path

from apps.onboarding.views import BuildConfigurationView, GenerateQuestionsView

urlpatterns = [
    path("generate-questions/", GenerateQuestionsView.as_view(), name="generate-questions"),
    path("build-configuration/", BuildConfigurationView.as_view(), name="build-configuration"),
]
