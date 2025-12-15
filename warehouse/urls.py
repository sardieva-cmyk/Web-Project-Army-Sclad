from django.urls import path
from . import views

urlpatterns = [
    # Главная страница — дашборд
    path('', views.dashboard, name='dashboard'),

    # Экспорт в Excel
    path('export/excel/', views.export_excel, name='export_excel'),

    # Экспорт в PDF
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]