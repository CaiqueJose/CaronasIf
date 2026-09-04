from .forms import CadastroForm
from django.shortcuts import render, redirect
from .models import *
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import time


@require_POST
def registrar_atividade(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {"autenticado": False},
            status=401
        )

    request.session["ultima_atividade"] = time.time()

    return JsonResponse({
        "autenticado": True
    })


def verificar_sessao(request):
    if request.user.is_authenticated:
        return JsonResponse({"autenticado": True})

    return JsonResponse(
        {"autenticado": False},
        status=401
    )


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Busca todas as caronas do banco de dados ordenando pelas mais recentes
        context['caronas'] = Carona.objects.all().order_by('-dataHora')
        return context


class CaronaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        caronas = Carona.objects.all()
        return render(request, 'carona.html', {'caronas': caronas})


class ChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        return render(request, 'chat.html', {'chats': chats})


class AvaliacaoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        avaliacoes = Avaliacao.objects.all()
        return render(request, 'avaliacao.html', {'avaliacoes': avaliacoes})


class PaisView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        paises = Pais.objects.all()
        return render(request, 'pais.html', {'paises': paises})


class EstadoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        estados = Estado.objects.all()
        return render(request, 'estado.html', {'estados': estados})


class CidadeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cidades = Cidade.objects.all()
        return render(request, 'cidade.html', {'cidades': cidades})