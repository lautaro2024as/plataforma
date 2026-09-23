"""
URL configuration for Plataforma_de_juegos project.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
