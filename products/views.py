from rest_framework.generics import GenericAPIView, DestroyAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.core.cache import cache

from .models import Product, Category, Comment
from .serializers import (ProductListSerializer,
                          ProductDetailSerializer,
                          CommentSerializer,
                          CategorySerializer)
from .filters import ProductFilter, BestSellingProductsOrder
from paginations import CustomPagination
from permissions import IsOwner, IsAuthenticated


class HomeAPIView(GenericAPIView):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()

    def get(self, request):
        new_products = self.queryset.order_by('-created')[:12]
        categories = Category.objects.filter(is_sub=False)

        new_products_serializer = self.serializer_class(new_products, many=True)
        categories_serializer = CategorySerializer(categories, many=True)
        
        return Response({
            'new_products': new_products_serializer.data,
            'categories':categories_serializer.data
        }, status=status.HTTP_200_OK)
    

class CategoryViewSet(ListModelMixin, GenericViewSet):
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, BestSellingProductsOrder, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    ordering_fields = ['created', 'price', 'bestselling']
    search_fields = ['name']
    pagination_class = CustomPagination

    def get_queryset(self):
        products = Product.objects.all()

        category_slug = self.kwargs.get('slug')
        category = Category.objects.get(slug=category_slug)
        if category.is_sub:
            products = products.filter(category=category)
        else:
            sub_categories = Category.objects.filter(sub_category=category)
            if sub_categories.exists():
                products = products.filter(category__in=sub_categories)
            else:
                products = products.filter(category=category)
            
        return products


class ProductDetailAPIView(GenericAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()

    def get(self, reqeust, slug):
        product = self.queryset.get(slug=slug)
        views = cache.get(product.id, 0) + 1
        cache.set(product.id, views)
        similar_products = self.queryset.filter(category=product.category).exclude(pk=product.id)[:4]

        serializer = self.serializer_class(product)
        similar_products_serializer = ProductListSerializer(similar_products, many=True)
        
        return Response({
            'product': serializer.data,
            'similar_products': similar_products_serializer.data
        }, status=status.HTTP_200_OK)


class AllProductsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, BestSellingProductsOrder, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    ordering_fields = ['created', 'price', 'bestselling']
    search_fields = ['name']
    pagination_class = CustomPagination


class CommentAPIView(GenericAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get(self, request, slug):
        product = Product.objects.get(slug=slug)
        comments = Comment.objects.filter(product=product, is_reply=False)
        serializer = self.serializer_class(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @permission_classes([IsAuthenticated])
    def post(self, request, slug):
        body = request.data.get('body')
        product = Product.objects.get(slug=slug)
        Comment.objects.create(user=request.user, product=product, body=body)
        return Response({'message':'Comment has been created'}, status=status.HTTP_201_CREATED)
    

class ReplyCommentAPIView(GenericAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug, comment_id):
        comment = Comment.objects.get(pk=comment_id)
        body = request.data.get('body')
        product = Product.objects.get(slug=slug)
        Comment.objects.create(user=request.user,
                               product=product,
                               body=body,
                               reply=comment,
                               is_reply=True)
        return Response({'message':'Reply comment has been created'}, status=status.HTTP_201_CREATED)


class DeleteCommentAPIView(DestroyAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]