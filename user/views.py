from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    PasswordUpdateSerializer
)
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

User = get_user_model()

class UserRegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({
                    'code': 0,
                    'message': '注册成功'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'code': 40003,
                    'message': '注册请求处理失败，请稍后再试'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)
            
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'code': 0,
                    'message': '登录成功',
                    'data': {
                        'token': str(refresh.access_token)
                    }
                })
            return Response({
                'code': 40003,
                'message': '密码错误'
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({
            'code': 0,
            'message': '获取成功',
            'data': serializer.data
        })

class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 0,
                'message': '更新成功'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = PasswordUpdateSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['password']):
                return Response({
                    'code': 40001,
                    'message': '原密码错误'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if serializer.validated_data['password'] == serializer.validated_data['new_password']:
                return Response({
                    'code': 40002,
                    'message': '新密码与旧密码一致'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({
                'code': 0,
                'message': '密码修改成功'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            request.user.delete()
            return Response({
                'code': 0,
                'message': '注销成功'
            })
        except Exception as e:
            return Response({
                'code': 40002,
                'message': '注销请求处理失败，请稍后再试'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserQuitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 从 header 中获取 token
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return Response({
                    'code': 40301,
                    'message': '请登录后操作'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 获取 token 字符串
            token = auth_header.split(' ')[1]
            
            # 将 token 加入黑名单
            try:
                token_obj = OutstandingToken.objects.get(token=token)
                BlacklistedToken.objects.get_or_create(token=token_obj)
            except OutstandingToken.DoesNotExist:
                pass
            
            return Response({
                'code': 0,
                'message': '退出成功'
            })
        except Exception as e:
            return Response({
                'code': 40301,
                'message': '请登录后操作'
            }, status=status.HTTP_403_FORBIDDEN)
