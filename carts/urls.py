from rest_framework_nested import routers
from . import views
from django.urls import path, include

router = routers.DefaultRouter()

router.register('carts', views.CartViewSet, basename='carts')
router.register('orders', views.OrderViewSet, basename='orders')

cart_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
cart_router.register('items', views.CartItemViewSet, basename="cart_items")

app_name = 'carts'
urlpatterns = [
    path('', include(router.urls)),
    path('', include(cart_router.urls)),
]