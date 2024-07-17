from .models import Cart, CartItem, Order, OrderItem, Coupon, Address
from django.contrib import admin

admin.site.register(Cart)

@admin.register(CartItem)
class CartItemsAdmin(admin.ModelAdmin):
    list_display = ['cart']

class AddressInLine(admin.TabularInline):
    model = Address
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [AddressInLine]
    list_display = ('id', 'placed_at', 'pending_status', 'owner')
    list_filter = ('pending_status', 'placed_at')
    search_fields = ('owner__full_name', 'owner__phone_number')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    raw_id_fields = ('order',)

admin.site.register(Coupon)

admin.site.register(Address)