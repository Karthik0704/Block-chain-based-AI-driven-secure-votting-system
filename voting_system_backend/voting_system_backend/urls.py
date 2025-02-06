from django.contrib import admin
from django.urls import path, include
from authentication import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", auth_views.home_page, name="home_page"),  # Home page route
    path("auth/", include("authentication.urls")),    # All auth-related routes
    path('auth/results/', include('authentication.urls')),
]
