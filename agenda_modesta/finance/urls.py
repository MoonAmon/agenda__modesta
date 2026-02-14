from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Orçamentos
    path('orcamentos/', views.orcamento_list, name='orcamentos'),
    path('orcamentos/novo/', views.orcamento_create, name='orcamento_create'),
    path('orcamentos/<uuid:pk>/editar/', views.orcamento_edit, name='orcamento_edit'),
    path('orcamentos/<uuid:pk>/excluir/', views.orcamento_delete, name='orcamento_delete'),
    path('orcamentos/<uuid:pk>/pago/', views.orcamento_marcar_pago, name='orcamento_marcar_pago'),
    path('orcamentos/<uuid:pk>/email/', views.orcamento_enviar_email, name='orcamento_enviar_email'),
    path('orcamentos/<uuid:pk>/pdf/', views.orcamento_pdf, name='orcamento_pdf'),
    path('orcamentos/pacote-info/', views.get_pacote_info, name='get_pacote_info'),

    # Recibos
    path('recibos/', views.recibo_list, name='recibos'),
    path('recibos/novo/', views.recibo_create, name='recibo_create'),
    path('recibos/<uuid:pk>/', views.recibo_detail, name='recibo_detail'),
    path('recibos/<uuid:pk>/excluir/', views.recibo_delete, name='recibo_delete'),
    path('recibos/<uuid:pk>/email/', views.recibo_enviar_email, name='recibo_enviar_email'),
    path('recibos/<uuid:pk>/pdf/', views.recibo_pdf, name='recibo_pdf'),
    path('recibos/from-orcamento/<uuid:pk>/', views.recibo_from_orcamento, name='recibo_from_orcamento'),

    # Pacotes
    path('pacotes/', views.pacote_list, name='pacotes'),
    path('pacotes/novo/', views.pacote_create, name='pacote_create'),
    path('pacotes/<uuid:pk>/editar/', views.pacote_edit, name='pacote_edit'),
    path('pacotes/<uuid:pk>/excluir/', views.pacote_delete, name='pacote_delete'),
]
