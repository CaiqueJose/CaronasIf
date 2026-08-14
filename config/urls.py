from django.contrib import admin
from django.urls import path
from app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('caronas/', CaronaView.as_view(), name='caronas'),
    path('chats/', ChatView.as_view(), name='chats'),
    path('avaliacoes/', AvaliacaoView.as_view(), name='avaliacoes'),
    path('paises/', PaisView.as_view(), name='paises'),
    path('estados/', EstadoView.as_view(), name='estados'),
    path('cidades/', CidadeView.as_view(), name='cidades'),
]