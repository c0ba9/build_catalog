from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    verbose_name = 'Дополнительное фото'
    verbose_name_plural = 'Дополнительные фото (галерея)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'unit', 'is_available', 'is_on_order', 'is_featured')
    list_filter = ('is_available', 'is_on_order', 'is_featured', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('price', 'is_available', 'is_on_order', 'is_featured')
    inlines = [ProductImageInline]