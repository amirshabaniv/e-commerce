from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from products.models import Product

User = get_user_model()

class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, blank=True, null=True, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cartitems')
    quantity = models.PositiveIntegerField(default=0)
    

class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    ]
    placed_at = models.DateTimeField(auto_now_add=True)
    pending_status = models.CharField(
        max_length=50, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    discount = models.IntegerField(blank=True, null=True, default=None)

    @property
    def total_price(self):
        items = self.items.select_related('product').all()
        total = sum([item.quantity * item.product.price for item in items])
        if self.discount:
            discount_price = (self.discount / 100) * total
            return int(total - discount_price)
        return total
    
    def __str__(self):
        return self.pending_status


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name = "items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()
    
    def __str__(self):
        return f'this orderitem have {self.quantity} of {self.product}'


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(90)])
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Address(models.Model):
    order = models.OneToOneField(Order, on_delete=models.DO_NOTHING, related_name='address')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address')
    postal_code = models.CharField(max_length=80)
    address = models.TextField()
    plaque = models.CharField(max_length=80)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.postal_code} - {self.user.phone_number}'
