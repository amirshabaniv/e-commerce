from rest_framework import serializers
from django.db import transaction

from .models import Cart, CartItem, Order, OrderItem, Address
from products.serializers import ProductListSerializer
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()
    sub_total = serializers.SerializerMethodField(method_name='total')

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'quantity', 'product', 'sub_total']

    def total(self, cartitem:CartItem):
        return cartitem.quantity * cartitem.product.price


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField(method_name='main_total') 

    class Meta:
        model = Cart
        fields = ['id', 'items', 'grand_total']
        extra_kwargs = {
            'id' : {'read_only':True},
        }
    
    def main_total(self, cart: Cart):
        items = cart.items.select_related('product').all()
        total = sum([item.quantity * item.product.price for item in items])
        return total


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    
    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('There is no product associated with the given ID')
        
        return value
    
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id'] 
        quantity = self.validated_data['quantity']
        
        try:
            cartitem = CartItem.objects.get(product_id=product_id, cart_id=cart_id)
            cartitem.quantity += quantity
            cartitem.save()
            self.instance = cartitem

        except:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
            
        return self.instance
         

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['id', 'quantity']
        extra_kwargs = {
            'id' : {'read_only':True},
        }


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()
    get_item_cost = serializers.SerializerMethodField(method_name='get_cost')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'get_item_cost']
    
    def get_cost(self, orderitem:OrderItem):
        return orderitem.product.price * orderitem.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'placed_at', 'pending_status', 'owner', 'discount', 'items', 'total_price']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    
    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('This cart_id is invalid')
        
        elif not CartItem.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError('Sorry your cart is empty')
        
        return cart_id
    
    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            user_id = self.context['user_id']
            order = Order.objects.create(owner_id = user_id)
            cartitems = CartItem.objects.filter(cart_id=cart_id)
            orderitems = [
                OrderItem(order=order, 
                    product=item.product, 
                    quantity=item.quantity
                    )
            for item in cartitems
            ]
            OrderItem.objects.bulk_create(orderitems)
            Cart.objects.filter(id=cart_id).delete()
            return order 


class UpdateOrderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Order 
        fields = ['pending_status']


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'postal_code', 'address', 'plaque', 'province', 'city']