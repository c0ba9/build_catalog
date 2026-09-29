from .models import Category

def categories_processor(request):
    """Передает список всех категорий с подкатегориями во все шаблоны сайта"""
    parent_categories = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children')
    return {
        'all_categories': parent_categories
    }