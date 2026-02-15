from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.agenda_list, name='list'),
    path('novo/', views.agenda_create, name='create'),
    path('<uuid:pk>/editar/', views.agenda_edit, name='edit'),
    path('<uuid:pk>/excluir/', views.agenda_delete, name='delete'),
    path('<uuid:pk>/confirmar/', views.toggle_confirmado, name='toggle_confirmado'),
    # HTMX – fluxo de agendamento em passos
    path('novo-agendamento/', views.novo_agendamento, name='novo_agendamento'),
    path('step1/', views.step1_projeto, name='step1_projeto'),
    path('step2/', views.step2_detalhes, name='step2_detalhes'),
    path('step3/', views.step3_confirmar, name='step3_confirmar'),
    path('projetos-por-cliente/', views.projetos_por_cliente, name='projetos_por_cliente'),
    path('api/week/', views.agenda_week_json, name='week_json'),
    # Google Calendar – bilateral sync
    path('google/webhook/', views.google_calendar_webhook, name='google_webhook'),
    path('google/registrar/', views.registrar_google_sync, name='google_registrar'),
    path('google/sincronizar/', views.sincronizar_google_agora, name='google_sincronizar'),
]
