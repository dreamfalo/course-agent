from django.urls import path, include
from rest_framework.routers import DefaultRouter
from config.views import ConfigViewSet, UserViewSet

router = DefaultRouter()
router.register(r"system", ConfigViewSet, basename="system_config")
router.register(r"user", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
