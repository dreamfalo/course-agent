from rest_framework import serializers
from config.models import SystemConfig, SystemUser


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ["id", "config_key", "config_value", "config_type", "category", "description", "is_active", "updated_at"]
        read_only_fields = ["id", "updated_at"]

    def validate_config_value(self, value):
        """根据 config_type 校验值格式"""
        ct = self.initial_data.get("config_type", "string")
        import json as _json
        if ct == "json":
            try:
                _json.loads(value)
            except _json.JSONDecodeError:
                raise serializers.ValidationError("配置值不是合法的 JSON")
        elif ct == "int":
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("配置值不是合法的整数")
        elif ct == "bool":
            if value.lower() not in ("true", "false", "1", "0"):
                raise serializers.ValidationError("配置值不是合法的布尔值")
        return value


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = SystemUser
        fields = ["id", "username", "password", "email", "role", "phone"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = SystemUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = SystemUser
        fields = ["id", "username", "email", "role", "phone", "password", "is_active", "date_joined"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
