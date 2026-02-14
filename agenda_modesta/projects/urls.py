from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('novo/', views.project_create, name='create'),
    path('<uuid:pk>/', views.project_detail, name='detail'),
    path('<uuid:pk>/editar/', views.project_edit, name='edit'),
    path('<uuid:pk>/excluir/', views.project_delete, name='delete'),
]
