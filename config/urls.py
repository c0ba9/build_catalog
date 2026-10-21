from django.contrib import admin
from django.urls import path
from catalog import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('catalog/<slug:category_slug>/', views.catalog_view, name='category_detail'),
    path('catalog/<slug:category_slug>/<slug:product_slug>/', views.product_detail_view, name='product_detail'),
    path('about/', views.about_view, name='about'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('delivery/', views.delivery_view, name='delivery'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
