from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Авторизация
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='/login/'
    ), name='logout'),

    # Дашборд и экспорт — только ОДНА строка!
    path('', include('warehouse.urls')),
]