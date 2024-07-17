from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.core.cache import cache
import requests
import json
import datetime
from django.http import HttpResponse

from .serializers import (CartSerializer, CartItemSerializer, 
                          AddCartItemSerializer, UpdateCartItemSerializer, 
                          OrderSerializer, CreateOrderSerializer, UpdateOrderSerializer, AddressSerializer)
from .models import Cart, CartItem, Order, Coupon, Address
from permissions import IsOwner2, IsAuthenticated


class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    
    http_method_names = ["get", "post", "patch", "delete"]
    
    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs["cart_pk"])
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        
        return CartItemSerializer
    
    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}

MERCHANT = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX'
ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"
CallbackURL = 'http://127.0.0.1:8000/orders/verify/?o_id='

class OrderViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    http_method_names = ["get", "patch", "post", "delete", "options", "head"]

    @action(detail=True, methods=['POST'])
    def address(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs.get('pk'))
        if order.owner == request.user:
            serializer = AddressSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            address, created = Address.objects.get_or_create(user=request.user, order=order)

            address.address = validated_data.get('address', address.address)
            address.postal_code = validated_data.get('postal_code', address.postal_code)
            address.plaque = validated_data.get('plaque', address.plaque)
            address.province = validated_data.get('province', address.province)
            address.city = validated_data.get('city', address.city)

            address.save()

            message = 'Address was created' if created else 'Address was updated'
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

            return Response({'message': message}, status=status_code)
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def copoun(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        code = request.data.get('code')
        try:
            coupon = Coupon.objects.get(code__exact=code, valid_from__lte=now, valid_to__gte=now, active=True)
        except Coupon.DoesNotExist:
            return Response({'error':'this coupon does not exists'}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.get(pk=self.kwargs.get('pk'))
        if order.owner == request.user:
            order.discount = coupon.discount
            order.save()
            return Response({'message':'Discount code applied'})
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def pay(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs.get('pk'))
        if order.owner == request.user:
            amount = order.total_price
            req_data = {
                "merchant_id": MERCHANT,
                "amount": amount,
                "callback_url": CallbackURL,
                "description": description,
                "metadata": {"mobile": request.user.phone_number, "full name": request.user.full_name}
            }
            req_header = {"accept": "application/json", "content-type": "application/json"}
            req = requests.post(url=ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)
            response_data = req.json()
            if 'authority' in response_data.get('data', {}):
                authority = response_data['data']['authority']
                return Response({"authority": authority})
            else:
                e_code = response_data.get('errors', {}).get('code', 'Unknown')
                e_message = response_data.get('errors', {}).get('message', 'Unknown error occurred')
                return Response({"error_code": e_code, "error_message": e_message})
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def verify(self, request):
        order_id = request.GET.get('o_id')
        order = Order.objects.get(pk=order_id)
        amount = order.total_price
        t_status = request.GET.get('Status')
        t_authority = request.GET['Authority']
        if request.GET.get('Status') == 'OK':
            req_header = {"accept": "application/json",
                            "content-type": "application/json'"}
            req_data = {
                "merchant_id": MERCHANT,
                "amount": amount,
                "authority": t_authority
            }
            req = requests.post(url=ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)
            if len(req.json()['errors']) == 0:
                t_status = req.json()['data']['code']
                if t_status == 100:
                    order.pending_status = 'C'
                    order.save()
                    return HttpResponse('Transaction success.\nRefID: ' + str(
                        req.json()['data']['ref_id']
                    ))
                elif t_status == 101:
                    return HttpResponse('Transaction submitted : ' + str(
                        req.json()['data']['message']
                    ))
                else:
                    return HttpResponse('Transaction failed.\nStatus: ' + str(
                        req.json()['data']['message']
                    ))
            else:
                e_code = req.json()['errors']['code']
                e_message = req.json()['errors']['message']
                return HttpResponse(f"Error code: {e_code}, Error Message: {e_message}")
        else:
            return HttpResponse('Transaction failed or canceled by user')

    def get_permissions(self):
        if self.request.method in ['GET', "PATCH", "DELETE"]:
            return [(IsAdminUser()) or (IsOwner2())]
        return [IsAuthenticated()]
            
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context={"user_id": self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer
       
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(owner=user)
    
    def get_serializer_context(self):
        return {"user_id": self.request.user.id}