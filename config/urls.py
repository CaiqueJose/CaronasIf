from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from app.views import *
from app.forms import LoginForm


urlpatterns = [

    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="login.html", authentication_form=LoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", RegisterView.as_view(), name="cadastro"),
    path("verificar-sessao/", verificar_sessao, name="verificar_sessao"),
    path("registrar-atividade/", registrar_atividade, name="registrar_atividade"),
    path("", IndexView.as_view(), name="index"),
    path("contador-conversas/", ContadorConversasView.as_view(), name="contador_conversas"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil-motorista/<int:motorista_id>/", PerfilMotoristaView.as_view(), name="perfil_motorista"),
    path("chat/motorista/<int:motorista_id>/", IniciarChatMotoristaView.as_view(), name="iniciar_chat_motorista"),
    path("caronas/", CaronaView.as_view(), name="caronas"),
    path("minhas-caronas/", MinhasCaronasView.as_view(), name="minhas_caronas"),
    path("verificacao-cnh/", VerificacaoCNHView.as_view(), name="verificacao_cnh"),
    path("caronas/criar/", CriarCaronaView.as_view(), name="criar_carona"),
    path("caronas/<int:pk>/editar/", EditarCaronaView.as_view(), name="editar_carona"),
    path("chats/", ChatView.as_view(), name="chats"),
    path("chats/contadores/", ContadoresChatView.as_view(), name="contadores_chat"),
    path("chat/<int:conversa_id>/", AbrirChatView.as_view(), name="abrir_chat"),
    path("chat/<int:conversa_id>/enviar/", EnviarMensagemView.as_view(), name="enviar_mensagem"),
    path("chat/<int:conversa_id>/mensagens/", BuscarMensagensView.as_view(), name="buscar_mensagens"),
    path("avaliacoes/", AvaliacaoView.as_view(), name="avaliacoes"),
    path("paises/", PaisView.as_view(), name="paises"),
    path("estados/", EstadoView.as_view(), name="estados"),
    path("cidades/", CidadeView.as_view(), name="cidades"),
]