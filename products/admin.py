from django.contrib import admin
from .models import Category, Product, ProImage, Comment


admin.site.register(Category)

class ProImageInlines(admin.TabularInline):
    model = ProImage
    raw_id_fields = ('product',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    raw_id_fields = ('category',)
    inlines = (ProImageInlines,)

admin.site.register(Comment)