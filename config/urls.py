from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import LogoutView

from studio.views import StudioLoginView, auth_signup, delete_account, home


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("login/", StudioLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", auth_signup, name="signup"),
    path("delete-account/", delete_account, name="delete_account"),
    path("projects/", include("studio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

