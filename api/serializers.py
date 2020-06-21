from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User

class MailSerializer(serializers.Serializer):
    recipient = serializers.EmailField()
    subject = serializers.CharField()
    body = serializers.CharField()
    cc = serializers.CharField(required=False, allow_blank=True)
    bcc = serializers.CharField(required=False, allow_blank=True)
    hour = serializers.CharField(required=False, allow_blank=True)

class TemplateMailSerializer(MailSerializer):
    body = None
    htmlBody = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')


class PasswordResetSerializer(serializers.ModelSerializer):
    """Serializer class for the Password Reset API View."""
    email = serializers.EmailField(source='User.email')
    password = serializers.CharField(source='User.password', style={'input_type': 'password'})
    new_password = serializers.CharField(source='User.password', style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('email', 'password', 'new_password')

    def update(self, instance, validated_data):
        # instance.username = validated_data.get('username', instance.username)
        # instance.email = validated_data.get('email', instance.email)
        instance.password = make_password(instance.password)
        instance.password = validated_data.get('password', instance.password)
        instance.save()
        return instance