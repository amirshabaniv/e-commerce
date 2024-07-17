from rest_framework import serializers
from django.core.validators import RegexValidator
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django.contrib.auth import get_user_model
User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2= serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model=User
        fields = ['phone_number', 'full_name', 'password', 'password2']

    def validate(self, attrs):
        password=attrs.get('password', '')
        password2 =attrs.get('password2', '')
        if password !=password2:
            raise serializers.ValidationError('passwords do not match')
         
        return attrs

    def create(self, validated_data):
        user= User(
            phone_number=validated_data['phone_number'],
            full_name=validated_data.get('full_name'),
            )
        user.set_password(validated_data['password'])
        user.save()
        return user


class VerifySerializer(serializers.Serializer):
    otp = serializers.CharField(validators=[RegexValidator(
        regex=r'^\d{5}$',
        message='otp code must be 5 digit',
        code='invalid_token'
    )])

    class Meta:
        fields = ['otp']

    def validate(self, attrs):
        otp = attrs.get('otp')
        if phone_number := self.verify_otp_code(otp):
            try:
                attrs['phone_number'] = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                raise ValueError('User not found')
        if not attrs.get('phone_number'):
            raise ValueError('the otp is expired or invalid')
        return attrs
    
    def verify_otp_code(self, otp):
        return cache.get(otp)
    

class LoginSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=11, min_length=6,validators=[RegexValidator(
                                         regex=r'^09\d{9}$',
                                         message='Phone number must be 11 digits only.')])
    password = serializers.CharField(max_length=68, write_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['phone_number', 'password', 'access_token', 'refresh_token']

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        request=self.context.get('request')
        user = authenticate(request, phone_number=phone_number, password=password)
        if not user:
            raise AuthenticationFailed('Invalid credential try again')
        if not user.is_verified:
            raise AuthenticationFailed('Phone number is not verified')
        tokens=user.tokens()
        return {
            'phone_number':user.phone_number,
            'access_token':str(tokens.get('access')),
            'refresh_token':str(tokens.get('refresh'))
        }


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11, min_length=6,validators=[RegexValidator(
                                         regex=r'^09\d{9}$',
                                         message='Phone number must be 11 digits only.')])
    
    class Meta:
        fields = ['phone_number']


class SetNewPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    otp=serializers.CharField(min_length=5, max_length=5, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'otp']

    def validate(self, attrs):
        otp = attrs.get('otp')
        if phone_number := self.verify_otp_code(otp):
            try:
                attrs['phone_number'] = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                raise ValueError('User not found')
        if not attrs.get('phone_number'):
            raise ValueError('the otp is expired or invalid')
        password=attrs.get('password')
        confirm_password=attrs.get('confirm_password')
        if password != confirm_password:
            raise ValueError('Passwords must be match')
        request=self.context.get('request')
        user = request.user
        user.set_password(password)
        user.save()
        return attrs
    
    def verify_otp_code(self, otp):
        return cache.get(otp)


class LogoutSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }
    
    def validate(self, attrs):
        self.token = attrs.get('refresh_token')

        return attrs

    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')

