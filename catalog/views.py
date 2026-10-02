from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Category, Product


def home_view(request):
    """
    Главная страница:
    - Загружает родительские категории с дочерними за 1 оптимизированный запрос
    - Хиты продаж (товары в наличии и под заказ)
    - Секция свежих поступлений убрана по требованию
    """
    parent_categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    
    featured_products = (
        Product.objects.filter(is_featured=True)
        .filter(Q(is_available=True) | Q(is_on_order=True))
        .select_related('category')[:8]
    )

    context = {
        'categories': parent_categories,
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)


def catalog_view(request, category_slug=None):
    """
    Каталог товаров:
    - Если category_slug не передан и нет поиска -> открываются плитки родительских категорий с фото
    - Если передана главная категория с подкатегориями -> открываются плитки подкатегорий с фото
    - Если передана конечная подкатегория или введен поиск -> выводятся карточки товаров с фильтрами
    """
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    products = Product.objects.select_related('category', 'category__parent').prefetch_related('images')
    
    current_category = None
    subcategories = []
    has_subcategories = False

    if category_slug:
        current_category = get_object_or_404(
            Category.objects.prefetch_related('children', 'parent'),
            slug=category_slug
        )
        children = list(current_category.children.all())
        if children:
            has_subcategories = True
            category_ids = [current_category.id] + [c.id for c in children]
            products = products.filter(category_id__in=category_ids)
            subcategories = children
        else:
            products = products.filter(category=current_category)
            if current_category.parent:
                subcategories = list(current_category.parent.children.all())

    # Полнотекстовый поиск по строке q (независимый от регистра: строчные, Заглавные, ВСЕ)
    query = request.GET.get('q', '').strip()
    is_root_catalog = bool(not category_slug and not query)
    show_all_products = bool(request.GET.get('view_all') == '1' or query)
    if query:
        # Варианты регистра для фразы: строчные, С заглавной, Каждое Слово С Заглавной, ВСЕ ЗАГЛАВНЫЕ
        q_lower = query.lower()
        q_cap = query.capitalize()
        q_title = query.title()
        q_upper = query.upper()
        variants = {query, q_lower, q_cap, q_title, q_upper}

        search_filter = Q()
        for var in variants:
            search_filter |= (
                Q(title__icontains=var) |
                Q(description__icontains=var) |
                Q(category__name__icontains=var) |
                Q(title__contains=var) |
                Q(description__contains=var) |
                Q(category__name__contains=var)
            )

        # Если поисковый запрос из нескольких слов (например: сайдинг брус)
        words = query.split()
        if len(words) > 1:
            words_filter = Q()
            for word in words:
                w_variants = {word, word.lower(), word.capitalize(), word.title(), word.upper()}
                word_q = Q()
                for wv in w_variants:
                    word_q |= (
                        Q(title__icontains=wv) |
                        Q(description__icontains=wv) |
                        Q(category__name__icontains=wv) |
                        Q(title__contains=wv) |
                        Q(description__contains=wv) |
                        Q(category__name__contains=wv)
                    )
                words_filter &= word_q
            search_filter |= words_filter

        products = products.filter(search_filter).distinct()

    # Фильтр по наличию
    availability = request.GET.get('availability', '')
    if availability == 'in_stock':
        products = products.filter(is_available=True)
    elif availability == 'on_order':
        products = products.filter(is_on_order=True)

    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'title':
        products = products.order_by('title')
    else:
        products = products.order_by('-created_at')

    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    context = {
        'category': current_category,
        'categories': categories,
        'parent_categories': categories,
        'subcategories': subcategories,
        'is_root_catalog': is_root_catalog,
        'has_subcategories': has_subcategories,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'query': query,
        'current_sort': sort,
        'availability': availability,
        'show_all_products': show_all_products,
    }
    return render(request, 'catalog.html', context)


def product_detail_view(request, category_slug, product_slug):
    """
    Страница отдельного товара с полным описанием и фотогалереей
    """
    product = get_object_or_404(
        Product.objects.select_related('category', 'category__parent').prefetch_related('images'),
        category__slug=category_slug,
        slug=product_slug
    )

    related_products = (
        Product.objects.filter(category=product.category)
        .filter(Q(is_available=True) | Q(is_on_order=True))
        .exclude(id=product.id)
        .select_related('category')[:4]
    )

    context = {
        'product': product,
        'category': product.category,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)


def about_view(request):
    """Страница 'О нас'"""
    return render(request, 'about.html')


def contacts_view(request):
    """Страница 'Контакты'"""
    return render(request, 'contacts.html')


def delivery_view(request):
    """Страница 'Доставка и оплата'"""
    return render(request, 'delivery.html')
