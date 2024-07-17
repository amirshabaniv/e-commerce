from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
import random
from django.core.cache import cache

from .serializers import (UserRegisterSerializer,
                          UserRegisterSerializer,
                          VerifySerializer,
                          LoginSerializer,
                          ForgotPasswordSerializer,
                          SetNewPasswordSerializer,
                          LogoutSerializer)
from utils import send_otp_code
from permissions import IsAuthenticated

from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterAPIView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            self.send_otp(serializer.validated_data['phone_number'])
            return Response({
                'data':serializer.data,
                'message':'thanks for signing up a otp code has be sent to verify your phone number'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_otp(self, phone_number):
        otp = random.randint(100000, 999999)
        send_otp_code.delay(phone_number, otp)
        cache.set(otp, phone_number, 120)


class VerifyAPIView(GenericAPIView):
    serializer_class = VerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.is_verified:
            user.is_verified = True
            user.save()
            return Response({
                'message':'account phone number verified successfully'
            }, status=status.HTTP_200_OK)
        return Response({'message':'user is already verified'}, status=status.HTTP_204_NO_CONTENT)


class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
  
    def post(self, request):
        serializer= self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.send_otp(serializer.validated_data['phone_number'])
            return Response({
                'message':'We sent a otp code to your phone number'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_otp(self, phone_number):
        otp = random.randint(10000, 99999)
        # send_otp_code.delay(phone_number, otp)
        cache.set(otp, phone_number, 120)


class SetNewPasswordAPIView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response({'success':True, 'message':"password reset is succesful"}, status=status.HTTP_200_OK)


class LogoutAPIView(GenericAPIView):
    serializer_class=LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'You logged out'}, status=status.HTTP_204_NO_CONTENT)