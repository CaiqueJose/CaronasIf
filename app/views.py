from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.views import View

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'index.html')

class CaronaView(View):
    def get(self, request, *args, **kwargs):
        caronas = Carona.objects.all()
        return render(request, 'carona.html', {'caronas':caronas})

class ChatView(View):
    def get(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        return render(request, 'chat.html', {'chats':chats})

class AvaliacaoView(View):
    def get(self, request, *args, **kwargs):
        avaliacoes = Avaliacao.objects.all()
        return render(request, 'avaliacao.html', {'avaliacoes':avaliacoes})

class PaisView(View):
    def get(self, request, *args, **kwargs):
        paises = Pais.objects.all()
        return render(request, 'pais.html', {'paises':paises})

class EstadoView(View):
    def get(self, request, *args, **kwargs):
        estados = Estado.objects.all()
        return render(request, 'estado.html', {'estados':estados})

class CidadeView(View):
    def get(self, request, *args, **kwargs):
        cidades = Cidade.objects.all()
        return render(request, 'cidade.html', {'cidades':cidades})