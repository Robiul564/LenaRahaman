"""URL configuration for the AI Agent Service."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/agent/", include("apps.agent.urls")),
    path("api/v1/onboarding/", include("apps.onboarding.urls")),
]
