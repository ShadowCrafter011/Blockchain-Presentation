from django.urls import path
from . import views

urlpatterns = [
    path('', views.root, name='root'),
    path("block/<str:hash>", views.block, name="block"),
    path("reset", views.reset, name="reset")
]