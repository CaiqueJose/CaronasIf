from datetime import time
import time as time_module
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import CadastroForm, UserProfileForm
from .models import *

@require_POST
def registrar_atividade(request):
    if not request.user.is_authenticated:
        return JsonResponse({"autenticado": False}, status=401)

    request.session["ultima_atividade"] = time_module.time()

    return JsonResponse({"autenticado": True})


def verificar_sessao(request):
    if request.user.is_authenticated:
        return JsonResponse({"autenticado": True})

    return JsonResponse({"autenticado": False}, status=401)


def usuario_eh_motorista(user):
    return user.groups.filter(name="Motorista").exists()


def usuario_eh_passageiro(user):
    return user.groups.filter(name="Passageiro").exists()


def usuario_eh_administrador(user):
    return user.groups.filter(name="Administrador").exists()


class MotoristaRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.perfil.is_verificado


class PassageiroRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Passageiro").exists()


class AdministradorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Administrador").exists()


class CriarCaronaView(LoginRequiredMixin, MotoristaRequiredMixin, CreateView):
    model = Carona
    template_name = "criar_carona.html"

    fields = ["origem", "destino", "dataHora", "valor", "vagas"]

    login_url = "/login/"

    def form_valid(self, form):
        form.instance.motorista = self.request.user
        return super().form_valid(form)


class EditarCaronaView(LoginRequiredMixin, MotoristaRequiredMixin, UpdateView):
    model = Carona
    template_name = "editar_carona.html"

    fields = [
        "origem",
        "destino",
        "dataHora",
        "valor",
        "vagas",
    ]

    login_url = "/login/"

    def test_func(self):
        if not super().test_func():
            return False

        carona = self.get_object()

        return carona.motorista == self.request.user


class AvaliarMotoristaView(
    LoginRequiredMixin, PassageiroRequiredMixin, CreateView
):
    model = Avaliacao
    template_name = "avaliar.html"

    fields = [
        "nota",
        "comentario",
    ]

    login_url = "/login/"


class AdministradorView(
    LoginRequiredMixin, AdministradorRequiredMixin, View
):
    def get(self, request, *args, **kwargs):
        return render(request, "administrador.html")


class RegisterView(View):
    def get(self, request):
        form = CadastroForm()
        return render(request, "register.html", {"form": form})

    def post(self, request):
        form = CadastroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
        return render(request, "register.html", {"form": form})


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        caronas = Carona.objects.select_related("motorista", "destino").annotate(
            media_avaliacao=Avg("motorista__avaliacoes__nota")
        )

        destino = self.request.GET.get("destino")
        data = self.request.GET.get("data")
        horario = self.request.GET.get("horario")

        if destino:
            caronas = caronas.filter(destino__nome__icontains=destino)

        if data:
            caronas = caronas.filter(dataHora__date=data)

        if horario == "manha":
            caronas = caronas.filter(
                dataHora__time__gte=time(6, 0), dataHora__time__lt=time(12, 0)
            )
        elif horario == "tarde":
            caronas = caronas.filter(
                dataHora__time__gte=time(12, 0), dataHora__time__lt=time(18, 0)
            )
        elif horario == "noite":
            caronas = caronas.filter(
                dataHora__time__gte=time(18, 0),
                dataHora__time__lt=time(23, 59, 59),
            )

        context["caronas"] = caronas.order_by("dataHora")

        return context


class CaronaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        caronas = Carona.objects.all()
        return render(request, "carona.html", {"caronas": caronas})


class ChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        return render(request, "chat.html", {"chats": chats})


class AvaliacaoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        avaliacoes = Avaliacao.objects.all()
        return render(request, "avaliacao.html", {"avaliacoes": avaliacoes})


class PaisView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        paises = Pais.objects.all()
        return render(request, "pais.html", {"paises": paises})


class EstadoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        estados = Estado.objects.all()
        return render(request, "estado.html", {"estados": estados})


class CidadeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cidades = Cidade.objects.all()
        return render(request, "cidade.html", {"cidades": cidades})


class DestinoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        destinos = Destino.objects.all()
        return render(request, "destino.html", {"destinos": destinos})


class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = 'perfil.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('perfil')

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Altera a senha caso receba dados de senha no POST
        if 'old_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Senha alterada com sucesso!")
                return redirect('perfil')
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
                return redirect('perfil')

        # Atualiza o perfil (incluindo validação de username)
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Informações atualizadas com sucesso!")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{error}")
        return redirect('perfil')


class PerfilMotoristaView(LoginRequiredMixin, View):
    def get(self, request, motorista_id):
        motorista = get_object_or_404(User, id=motorista_id)

        media_avaliacao = Avaliacao.objects.filter(
            motorista=motorista
        ).aggregate(
            media=Avg("nota")
        )["media"]

        avaliacoes = Avaliacao.objects.filter(
            motorista=motorista
        )

        return render(
            request,
            "perfil_motorista.html",
            {
                "motorista": motorista,
                "media_avaliacao": media_avaliacao,
                "avaliacoes": avaliacoes,
            }
        )