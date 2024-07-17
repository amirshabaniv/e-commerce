from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('products', views.AllProductsViewSet, basename='all_products')
router.register('categories/(?P<slug>[^/.]+)', views.CategoryViewSet, basename='category_filter')


app_name = 'products'
urlpatterns = [
    path('', include(router.urls)),
    path('home/', views.HomeAPIView.as_view(), name='home'),
    path('products/<slug:slug>/', views.ProductDetailAPIView.as_view(), name='product_detail'),
    
    path('products/<slug:slug>/comment/', views.CommentAPIView.as_view(), name='product_comment'),
    path('delete/comment/<int:pk>/', views.DeleteCommentAPIView.as_view(), name='delete_comment'),
    path('create/reply/<slug:slug>/<int:comment_id>/', views.ReplyCommentAPIView.as_view(), name='create-reply'),
]