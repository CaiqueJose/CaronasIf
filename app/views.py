from django.contrib.auth.decorators import login_required
from .forms import CadastroForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class RegisterView(View):
    def get(self, request):
        form = CadastroForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CadastroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'register.html', {'form': form})


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        print("USUÁRIO:", request.user)
        print("AUTENTICADO:", request.user.is_authenticated)

        return super().dispatch(request, *args, **kwargs)
class CaronaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        caronas = Carona.objects.all()
        return render(request, 'carona.html', {'caronas':caronas})

class ChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        return render(request, 'chat.html', {'chats':chats})

class AvaliacaoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        avaliacoes = Avaliacao.objects.all()
        return render(request, 'avaliacao.html', {'avaliacoes':avaliacoes})

class PaisView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        paises = Pais.objects.all()
        return render(request, 'pais.html', {'paises':paises})

class EstadoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        estados = Estado.objects.all()
        return render(request, 'estado.html', {'estados':estados})

class CidadeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cidades = Cidade.objects.all()
        return render(request, 'cidade.html', {'cidades':cidades})
