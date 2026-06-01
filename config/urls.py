from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from studio.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("projects/", include("studio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

