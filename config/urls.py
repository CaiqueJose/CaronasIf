from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from app.views import *
from app.forms import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', RegisterView.as_view(), name='cadastro'),
    path("verificar-sessao/", verificar_sessao, name="verificar_sessao"),
    path("registrar-atividade/", registrar_atividade, name="registrar_atividade"),
    path('', IndexView.as_view(), name='index'),
    path('caronas/', CaronaView.as_view(), name='caronas'),
    path('chats/', ChatView.as_view(), name='chats'),
    path('avaliacoes/', AvaliacaoView.as_view(), name='avaliacoes'),
    path('paises/', PaisView.as_view(), name='paises'),
    path('estados/', EstadoView.as_view(), name='estados'),
    path('cidades/', CidadeView.as_view(), name='cidades'),
    path('destinos/', DestinoView.as_view(), name='destinos'),
]