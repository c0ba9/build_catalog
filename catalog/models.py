from django.db import models
from django.urls import reverse
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def extend_sqlite_functions(sender, connection, **kwargs):
    """
    Обеспечивает корректный регистронезависимый поиск (case-insensitive LIKE)
    для русских букв (кириллицы) в базе данных SQLite.
    """
    if connection.vendor == 'sqlite':
        def sqlite_like(pattern, string, escape=None):
            if string is None or pattern is None:
                return False
            pat = str(pattern).lower().replace('%', '')
            if escape:
                pat = pat.replace(escape, '')
            return pat in str(string).lower()

        connection.connection.create_function('LIKE', 3, sqlite_like)
        connection.connection.create_function('LIKE', 2, lambda pat, s: sqlite_like(pat, s))
        connection.connection.create_function('LOWER', 1, lambda s: str(s).lower() if s is not None else '')
        connection.connection.create_function('UPPER', 1, lambda s: str(s).upper() if s is not None else '')


class Category(models.Model):
    name = models.CharField('Название категории', max_length=100)
    slug = models.SlugField('URL-слаг', unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        blank=True,
        null=True,
        verbose_name='Родительская категория'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'category_slug': self.slug})


class Product(models.Model):
    UNIT_CHOICES = (
        ('sq_m', 'м²'),
        ('pcs', 'шт.'),
        ('r_m', 'п.м.'),
        ('pack', 'упак.'),
    )

    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Категория'
    )
    title = models.CharField('Название товара', max_length=200)
    slug = models.SlugField('URL-слаг', unique=True, null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='sq_m')
    image = models.ImageField('Главное изображение', upload_to='products/', blank=True, null=True)
    
    is_available = models.BooleanField('В наличии', default=True)
    is_on_order = models.BooleanField('Под заказ', default=False)
    is_featured = models.BooleanField('Популярный товар (на главную)', default=False)
    
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.slug:
            return reverse('product_detail', kwargs={
                'category_slug': self.category.slug,
                'product_slug': self.slug
            })
        return reverse('category_detail', kwargs={'category_slug': self.category.slug})

    @property
    def availability_text(self):
        if self.is_available:
            return "В наличии"
        if self.is_on_order:
            return "Под заказ"
        return "Уточняйте наличие"

    @property
    def availability_css_class(self):
        if self.is_available:
            return "available"
        if self.is_on_order:
            return "on-order"
        return "unavailable"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images', 
        verbose_name='Товар'
    )
    image = models.ImageField('Дополнительное фото', upload_to='products/gallery/')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Галерея изображений'
        ordering = ['id']
