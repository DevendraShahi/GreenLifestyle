from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core app (homepage)
    path('', include('core.urls')),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    path('tips/', include('tips.urls')),
    
    path('administration/', include('administration.urls')),
]

# Serve static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
