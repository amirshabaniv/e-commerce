from .models import Product, ProImage, Comment, Category

from rest_framework import serializers
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProImage
        fields = ['id', 'product', 'image']


class ProductDetailSerializer(serializers.ModelSerializer):
    product_views = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child = serializers.ImageField(max_length = 1000000, allow_empty_file = False, use_url = False),
        write_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description',
                  'available', 'price', 'category_name',
                  'created', 'updated', 'images','uploaded_images', 'product_views']
        
    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images")
        product = Product.objects.create(**validated_data)
        for image in uploaded_images:
            newproduct_image = ProImage.objects.create(product=product, image=image)
        return product
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_product_views(self, obj):
        return cache.get(obj.id)


class ProductListSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'product_image', 'created']

    def get_product_image(self, obj):
        return ProImage.objects.filter(product=obj).first().image.url


class ReplySerializer(serializers.ModelSerializer):
    user_fullname = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user_fullname', 'body', 'created_at']
    
    def get_user_fullname(self, obj):
        return obj.user.full_name


class CommentSerializer(serializers.ModelSerializer):
    user_fullname = serializers.SerializerMethodField()
    rcomments = ReplySerializer(many=True)

    class Meta:
        model = Comment
        fields = ['id', 'user_fullname', 'body', 'created_at', 'rcomments']

    def get_user_fullname(self, obj):
        return obj.user.full_name


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['name']