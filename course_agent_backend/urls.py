"""课程助手后端总路由"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.views.static import serve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API 文档
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    # 业务接口
    path("api/schedule/", include("schedule.urls")),
    path("api/knowledge/", include("knowledge.urls")),
    path("api/task/", include("task.urls")),
    path("api/config/", include("config.urls")),
    path("api/agent/", include("agent_chat.urls")),
]

# Django 托管 Vue 前端
urlpatterns += [
    # 静态资源
    re_path(r"^assets/(?P<path>.*)$", serve, {"document_root": settings.VUE_DIST / "assets"}),
    # SPA 兜底 - 所有非 API 路径返回 index.html
    re_path(r"^(?!api/).*$", TemplateView.as_view(template_name="index.html")),
]