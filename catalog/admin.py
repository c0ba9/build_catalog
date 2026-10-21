from django.contrib import admin
from django.utils.html import mark_safe
from django.contrib import messages
from .models import Category, Product, ProductImage
from django.utils.html import format_html, mark_safe


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    verbose_name = 'Дополнительное фото'
    verbose_name_plural = 'Дополнительные фото (галерея)'


def _has_category_image_column():
    """
    Проверяет, существует ли колонка 'image' в таблице БД 'catalog_category'.
    Предотвращает падение админки (OperationalError: no such column: catalog_category.image),
    если пользователь еще не применил миграцию (python manage.py migrate).
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            table_desc = connection.introspection.get_table_description(cursor, 'catalog_category')
            cols = [col.name.lower() for col in table_desc]
            return 'image' in cols
    except Exception:
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_thumbnail', 'parent', 'slug', 'children_count')
    list_display_links = ('name', 'image_thumbnail')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('parent').prefetch_related('children')
        if not _has_category_image_column():
            qs = qs.defer('image', 'parent__image')
        return qs

    def changelist_view(self, request, extra_context=None):
        if not _has_category_image_column():
            messages.warning(
                request,
                'Внимание: колонка "image" еще не добавлена в таблицу базы данных. '
                'Для полноценной загрузки фото выполните: python manage.py migrate'
            )
        return super().changelist_view(request, extra_context=extra_context)

    def get_fields(self, request, obj=None):
        base_fields = ['name', 'slug', 'parent']
        if any(f.name == 'image' for f in self.model._meta.fields):
            base_fields.append('image')
            if obj and getattr(obj, 'image', None) and bool(getattr(obj.image, 'name', None)):
                base_fields.append('image_preview_large')
        return base_fields

    def get_readonly_fields(self, request, obj=None):
        if obj and getattr(obj, 'image', None) and bool(getattr(obj.image, 'name', None)):
            return ('image_preview_large',)
        return ()

    @admin.display(description='Фото', ordering='name')
    def image_thumbnail(self, obj):
        if not _has_category_image_column():
            return mark_safe('<span style="color: #d97706; font-size: 11px;">Требуется migrate</span>')
        try:
            image = getattr(obj, 'image', None)
            if image and hasattr(image, 'url') and bool(getattr(image, 'name', None)):
                return mark_safe(
                    f'<img src="{image.url}" alt="{obj.name}" '
                    f'style="width: 48px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />'
                )
        except Exception:
            pass
        return mark_safe('<span style="color: #999; font-size: 11px;">Нет фото</span>')

    @admin.display(description='Предпросмотр текущего фото')
    def image_preview_large(self, obj):
        try:
            image = getattr(obj, 'image', None)
            if image and hasattr(image, 'url') and bool(getattr(image, 'name', None)):
                return mark_safe(
                    f'<div style="display: inline-block;">'
                    f'<img src="{image.url}" alt="{obj.name}" style="max-width: 280px; max-height: 180px; object-fit: cover; border-radius: 6px; border: 1px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                    f'<div style="font-size: 11px; color: #666; margin-top: 4px;">Текущее изображение категории (плитка в каталоге)</div>'
                    f'</div>'
                )
        except Exception:
            pass
        return 'Изображение еще не выбрано. Выберите файл в поле выше и сохраните категорию.'

    @admin.display(description='Подкатегории')
    def children_count(self, obj):
        try:
            count = obj.children.count()
            if count > 0:
                return f"{count} подкатегорий"
        except Exception:
            pass
        return "—"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'unit', 'is_available', 'is_on_order', 'is_featured')
    list_filter = ('is_available', 'is_on_order', 'is_featured', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('price', 'is_available', 'is_on_order', 'is_featured')
    inlines = [ProductImageInline]