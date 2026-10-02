from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    verbose_name = 'Дополнительное фото'
    verbose_name_plural = 'Дополнительные фото (галерея)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_thumbnail', 'name', 'parent', 'slug', 'children_count')
    list_display_links = ('image_thumbnail', 'name')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    search_fields = ('name',)

    def get_fields(self, request, obj=None):
        base_fields = ['name', 'slug', 'parent']
        # Безопасно проверяем, добавлено ли поле image в models.py
        if any(f.name == 'image' for f in self.model._meta.fields):
            base_fields.extend(['image', 'image_preview_large'])
        return base_fields

    def get_readonly_fields(self, request, obj=None):
        if any(f.name == 'image' for f in self.model._meta.fields):
            return ('image_preview_large',)
        return ()

    def image_thumbnail(self, obj):
        # Безопасное получение поля image через getattr
        image = getattr(obj, 'image', None)
        if image and hasattr(image, 'url'):
            try:
                return mark_safe(f'<img src="{image.url}" style="width: 48px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />')
            except Exception:
                pass
        return mark_safe('<span style="color: #999; font-size: 11px;">Нет фото</span>')
    image_thumbnail.short_description = 'Фото'

    def image_preview_large(self, obj):
        image = getattr(obj, 'image', None)
        if image and hasattr(image, 'url'):
            try:
                return mark_safe(f'<img src="{image.url}" style="max-width: 260px; max-height: 180px; object-fit: cover; border-radius: 6px; border: 1px solid #ccc;" />')
            except Exception:
                pass
        return 'Изображение еще не загружено. Выберите файл выше и нажмите "Сохранить".'
    image_preview_large.short_description = 'Предпросмотр текущего фото'

    def children_count(self, obj):
        try:
            count = obj.children.count()
            if count > 0:
                return f"{count} подкатегорий"
        except Exception:
            pass
        return "—"
    children_count.short_description = 'Подкатегории'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'unit', 'is_available', 'is_on_order', 'is_featured')
    list_filter = ('is_available', 'is_on_order', 'is_featured', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('price', 'is_available', 'is_on_order', 'is_featured')
    inlines = [ProductImageInline]