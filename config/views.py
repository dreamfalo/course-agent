"""系统配置 + 用户管理"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from config.models import SystemConfig, SystemUser
from config.serializers import (
    SystemConfigSerializer, UserRegisterSerializer, UserSerializer,
)


class ConfigViewSet(viewsets.ModelViewSet):
    """系统配置管理（仅管理员）"""
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SystemConfig.objects.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.config_type == "secret":
            return Response({"code": 403, "msg": "密钥类配置不可通过接口修改", "data": None}, status=403)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"code": 0, "msg": "更新成功", "data": serializer.data})

    @action(detail=False, methods=["get"])
    def public(self, request):
        """公开配置（无需完整鉴权，用于前端初始化）"""
        qs = SystemConfig.objects.filter(is_active=True).exclude(config_type="secret")
        data = {c.config_key: c.config_value for c in qs}
        return Response({"code": 0, "msg": "ok", "data": data})


class UserViewSet(viewsets.ModelViewSet):
    """用户管理"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return SystemUser.objects.all()
        return SystemUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """用户注册"""
        ser = UserRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({
            "code": 0, "msg": "注册成功",
            "data": {"id": user.id, "username": user.username},
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get", "patch", "put"])
    def me(self, request):
        """获取或更新当前用户信息"""
        if request.method == "GET":
            return Response({"code": 0, "msg": "ok", "data": UserSerializer(request.user).data})
        # PATCH/PUT: update current user
        ser = UserSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"code": 0, "msg": "更新成功", "data": UserSerializer(request.user).data})
