from .models import Product

from django_filters import rest_framework as filters
from rest_framework import filters as OrderFilters
from django.db.models import Count, Q
from carts.models import Order


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price']


class BestSellingProductsOrder(filters.OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        popular_products = Product.objects.annotate(
            bestselling=Count('orderitem__order', filter=Q(orderitem__order__pending_status=Order.PAYMENT_STATUS_COMPLETE))
        ).order_by('-bestselling')
        return popular_products
    
    def get_schema_operation_parameters(self, views):
        return []
    