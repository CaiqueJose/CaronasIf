from datetime import time
import time as time_module
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Avg, Q, Exists, OuterRef
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView, UpdateView
from django.utils import timezone

from app.forms import CadastroForm, LoginForm, UserProfileForm

from app.models import (
    Pais,
    Estado,
    Cidade,
    Destino,
    Carona,
    Conversa,
    Mensagem,
    Avaliacao,
)


@require_POST
def registrar_atividade(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {"autenticado": False},
            status=401
        )

    request.session["ultima_atividade"] = time_module.time()

    return JsonResponse(
        {"autenticado": True}
    )


def verificar_sessao(request):

    if request.user.is_authenticated:
        return JsonResponse(
            {"autenticado": True}
        )

    return JsonResponse(
        {"autenticado": False},
        status=401
    )


class RegisterView(View):

    def get(self, request):

        form = CadastroForm()

        return render(
            request,
            "register.html",
            {
                "form": form
            }
        )

    def post(self, request):

        form = CadastroForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect("login")

        return render(
            request,
            "register.html",
            {
                "form": form
            }
        )


class IndexView(
    LoginRequiredMixin,
    TemplateView
):

    template_name = "index.html"
    login_url = "/login/"

    def get_context_data(
        self,
        **kwargs
    ):

        context = super().get_context_data(
            **kwargs
        )

        caronas = (
            Carona.objects
            .select_related(
                "motorista",
                "destino"
            )
            .annotate(
                media_avaliacao=Avg(
                    "motorista__avaliacoes_recebidas__nota"
                ),
                total_avaliacoes=Count(
                    "motorista__avaliacoes_recebidas"
                )
            )
        )

        destinos = Destino.objects.all()

        destino = self.request.GET.get(
            "destino"
        )

        data = self.request.GET.get(
            "data"
        )

        horario = self.request.GET.get(
            "horario"
        )

        if destino:

            caronas = caronas.filter(
                destino__nome__icontains=destino
            )

        if data:

            caronas = caronas.filter(
                data_hora__date=data
            )

        if horario == "manha":

            caronas = caronas.filter(
                data_hora__time__gte=time(6, 0),
                data_hora__time__lt=time(12, 0)
            )

        elif horario == "tarde":

            caronas = caronas.filter(
                data_hora__time__gte=time(12, 0),
                data_hora__time__lt=time(18, 0)
            )

        elif horario == "noite":

            caronas = caronas.filter(
                data_hora__time__gte=time(18, 0),
                data_hora__time__lt=time(23, 59, 59)
            )

        context["caronas"] = (
            caronas.order_by("data_hora")
        )

        context["destinos"] = destinos

        conversas_com_mensagens_novas = (
            Conversa.objects
            .filter(participantes=self.request.user)
            .filter(
                Exists(
                    Mensagem.objects.filter(
                        conversa=OuterRef('pk'),
                        lida=False
                    ).exclude(
                        remetente=self.request.user
                    )
                )
            )
            .distinct()
            .count()
        )

        context[
            "conversas_com_mensagens_novas"
        ] = conversas_com_mensagens_novas

        return context


class ContadorConversasView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        quantidade = (
            Conversa.objects
            .filter(participantes=request.user)
            .filter(
                Exists(
                    Mensagem.objects.filter(
                        conversa=OuterRef('pk'),
                        lida=False
                    ).exclude(
                        remetente=request.user
                    )
                )
            )
            .distinct()
            .count()
        )

        return JsonResponse(
            {
                "quantidade": quantidade
            }
        )


class CaronaView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        caronas = (
            Carona.objects
            .select_related(
                "motorista",
                "origem",
                "destino"
            )
            .order_by(
                "data_hora"
            )
        )

        return render(
            request,
            "carona.html",
            {
                "caronas": caronas
            }
        )


class MinhasCaronasView(
    LoginRequiredMixin,
    View
):

    login_url = "/login/"

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        caronas = (
            Carona.objects
            .filter(
                motorista=request.user
            )
            .select_related(
                "origem",
                "destino"
            )
            .order_by(
                "data_hora"
            )
        )

        return render(
            request,
            "carona.html",
            {
                "caronas": caronas
            }
        )


class CriarCaronaView(
    LoginRequiredMixin,
    View
):

    login_url = "/login/"

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        return render(
            request,
            "criar_carona.html"
        )

    def post(
        self,
        request,
        *args,
        **kwargs
    ):

        origem = request.POST.get(
            "origem"
        )

        destino = request.POST.get(
            "destino"
        )

        data_hora = request.POST.get(
            "data_hora"
        )

        valor = request.POST.get(
            "valor"
        )

        vagas = request.POST.get(
            "vagas"
        )

        Carona.objects.create(
            motorista=request.user,
            origem_id=origem,
            destino_id=destino,
            data_hora=data_hora,
            valor=valor,
            vagas=vagas
        )

        return redirect(
            "minhas_caronas"
        )


class EditarCaronaView(
    LoginRequiredMixin,
    View
):

    login_url = "/login/"

    def get(
        self,
        request,
        pk,
        *args,
        **kwargs
    ):

        carona = get_object_or_404(
            Carona,
            pk=pk
        )

        if carona.motorista != request.user:
            return HttpResponseForbidden(
                "Você não pode editar esta carona."
            )

        return render(
            request,
            "editar_carona.html",
            {
                "carona": carona
            }
        )

    def post(
        self,
        request,
        pk,
        *args,
        **kwargs
    ):

        carona = get_object_or_404(
            Carona,
            pk=pk
        )

        if carona.motorista != request.user:
            return HttpResponseForbidden(
                "Você não pode editar esta carona."
            )

        carona.origem_id = request.POST.get(
            "origem"
        )

        carona.destino_id = request.POST.get(
            "destino"
        )

        carona.data_hora = request.POST.get(
            "data_hora"
        )

        carona.valor = request.POST.get(
            "valor"
        )

        carona.vagas = request.POST.get(
            "vagas"
        )

        carona.save()

        return redirect(
            "minhas_caronas"
        )


class VerificacaoCNHView(
    LoginRequiredMixin,
    View
):

    login_url = "/login/"

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        perfil = getattr(
            request.user,
            "perfil",
            None
        )

        verificado = getattr(
            perfil,
            "is_verificado",
            False
        )

        return render(
            request,
            "verificacao_cnh.html",
            {
                "enviado": False,
                "verificado": verificado
            }
        )

    def post(
        self,
        request,
        *args,
        **kwargs
    ):

        nome = request.POST.get(
            "nome",
            ""
        ).strip()

        sobrenome = request.POST.get(
            "sobrenome",
            ""
        ).strip()

        usuario = request.POST.get(
            "usuario",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        if not nome or not sobrenome or not usuario or not email:

            return render(
                request,
                "verificacao_cnh.html",
                {
                    "enviado": False,
                    "erro":
                        "Preencha todos os campos."
                }
            )

        perfil = getattr(
            request.user,
            "perfil",
            None
        )

        verificado = getattr(
            perfil,
            "is_verificado",
            False
        )

        return render(
            request,
            "verificacao_cnh.html",
            {
                "enviado": True,
                "verificado": verificado,
                "nome": nome,
                "sobrenome": sobrenome,
                "usuario": usuario,
                "email": email
            }
        )


class ChatView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        conversas = (
            Conversa.objects
            .filter(
                participantes=request.user
            )
            .annotate(
                mensagens_nao_lidas=Count(
                    "mensagens",
                    filter=(
                        Q(
                            mensagens__lida=False
                        )
                        &
                        ~Q(
                            mensagens__remetente=request.user
                        )
                    ),
                    distinct=True
                )
            )
            .prefetch_related(
                "participantes"
            )
            .order_by(
                "-criado_em"
            )
        )

        return render(
            request,
            "chat.html",
            {
                "conversas": conversas
            }
        )


class AbrirChatView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        conversa_id,
        *args,
        **kwargs
    ):

        conversa = get_object_or_404(
            Conversa.objects.prefetch_related(
                "participantes",
                "mensagens__remetente"
            ),
            id=conversa_id
        )

        if not conversa.participantes.filter(
            id=request.user.id
        ).exists():

            return HttpResponseForbidden(
                "Você não participa desta conversa."
            )

        conversa.mensagens.filter(
            lida=False
        ).exclude(
            remetente=request.user
        ).update(
            lida=True
        )

        conversas = (
            Conversa.objects
            .filter(
                participantes=request.user
            )
            .annotate(
                mensagens_nao_lidas=Count(
                    "mensagens",
                    filter=(
                        Q(
                            mensagens__lida=False
                        )
                        &
                        ~Q(
                            mensagens__remetente=request.user
                        )
                    ),
                    distinct=True
                )
            )
            .prefetch_related(
                "participantes"
            )
            .order_by(
                "-criado_em"
            )
        )

        mensagens = (
            conversa.mensagens
            .select_related(
                "remetente"
            )
            .order_by(
                "enviado_em"
            )
        )

        return render(
            request,
            "chat.html",
            {
                "conversas": conversas,
                "conversa": conversa,
                "mensagens": mensagens
            }
        )


class ContadoresChatView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        conversas = (
            Conversa.objects
            .filter(participantes=request.user)
            .annotate(
                mensagens_nao_lidas=Count(
                    "mensagens",
                    filter=(
                        Q(mensagens__lida=False)
                        &
                        ~Q(mensagens__remetente=request.user)
                    ),
                    distinct=True
                )
            )
        )

        contadores = {
            str(conversa.id):
                conversa.mensagens_nao_lidas
            for conversa in conversas
        }

        return JsonResponse(
            {
                "contadores": contadores
            }
        )


class EnviarMensagemView(
    LoginRequiredMixin,
    View
):

    def post(
        self,
        request,
        conversa_id,
        *args,
        **kwargs
    ):

        conversa = get_object_or_404(
            Conversa,
            id=conversa_id
        )

        if not conversa.participantes.filter(
            id=request.user.id
        ).exists():

            return JsonResponse(
                {
                    "sucesso": False,
                    "erro":
                        "Você não participa desta conversa."
                },
                status=403
            )

        texto = request.POST.get(
            "texto",
            ""
        ).strip()

        if not texto:

            return JsonResponse(
                {
                    "sucesso": False,
                    "erro":
                        "A mensagem não pode estar vazia."
                },
                status=400
            )

        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            texto=texto
        )

        return JsonResponse(
            {
                "sucesso": True,
                "id": mensagem.id,
                "texto": mensagem.texto,
                "remetente":
                    mensagem.remetente.username,
                "remetente_id":
                    mensagem.remetente.id,
                "enviado_em": timezone.localtime(mensagem.enviado_em).strftime("%d/%m/%Y %H:%M"),
            }
        )


class BuscarMensagensView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        conversa_id,
        *args,
        **kwargs
    ):

        conversa = get_object_or_404(
            Conversa,
            id=conversa_id
        )

        if not conversa.participantes.filter(
            id=request.user.id
        ).exists():

            return JsonResponse(
                {
                    "erro":
                        "Você não participa desta conversa."
                },
                status=403
            )

        conversa.mensagens.filter(
            lida=False
        ).exclude(
            remetente=request.user
        ).update(
            lida=True
        )

        mensagens = (
            conversa.mensagens
            .select_related(
                "remetente"
            )
            .order_by(
                "enviado_em"
            )
        )

        dados = []

        for mensagem in mensagens:

            dados.append(
                {
                    "id": mensagem.id,
                    "texto": mensagem.texto,
                    "remetente":
                        mensagem.remetente.username,
                    "remetente_id":
                        mensagem.remetente.id,
                    "enviado_em": timezone.localtime(mensagem.enviado_em).strftime("%d/%m/%Y %H:%M"),
                    "lida":
                        mensagem.lida
                }
            )

        return JsonResponse(
            {
                "mensagens": dados
            }
        )


class IniciarChatMotoristaView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        motorista_id
    ):

        motorista = get_object_or_404(
            User,
            id=motorista_id
        )

        if motorista == request.user:

            return redirect(
                "perfil_motorista",
                motorista_id=motorista_id
            )

        conversa = (
            Conversa.objects
            .filter(
                participantes=request.user
            )
            .filter(
                participantes=motorista
            )
            .first()
        )

        if not conversa:

            conversa = Conversa.objects.create()

            conversa.participantes.add(
                request.user
            )

            conversa.participantes.add(
                motorista
            )

        return redirect(
            "abrir_chat",
            conversa_id=conversa.id
        )


class PerfilView(
    LoginRequiredMixin,
    UpdateView
):

    template_name = "perfil.html"

    form_class = UserProfileForm

    success_url = reverse_lazy(
        "perfil"
    )

    def get_object(self):

        return self.request.user

    def post(
        self,
        request,
        *args,
        **kwargs
    ):

        self.object = self.get_object()

        if "old_password" in request.POST:

            password_form = PasswordChangeForm(
                request.user,
                request.POST
            )

            if password_form.is_valid():

                user = password_form.save()

                update_session_auth_hash(
                    request,
                    user
                )

                messages.success(
                    request,
                    "Senha alterada com sucesso!"
                )

                return redirect(
                    "perfil"
                )

            for field, errors in (
                password_form.errors.items()
            ):

                for error in errors:

                    messages.error(
                        request,
                        error
                    )

            return redirect(
                "perfil"
            )

        form = self.get_form()

        if form.is_valid():

            return self.form_valid(
                form
            )

        return self.form_invalid(
            form
        )

    def form_valid(
        self,
        form
    ):

        form.save()

        messages.success(
            self.request,
            "Informações atualizadas com sucesso!"
        )

        return super().form_valid(
            form
        )

    def form_invalid(
        self,
        form
    ):

        for field, errors in (
            form.errors.items()
        ):

            for error in errors:

                messages.error(
                    self.request,
                    error
                )

        return redirect(
            "perfil"
        )


class PerfilMotoristaView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        motorista_id
    ):

        motorista = get_object_or_404(
            User,
            id=motorista_id
        )

        avaliacoes = (
            Avaliacao.objects
            .filter(
                motorista=motorista
            )
        )

        media_avaliacao = (
            avaliacoes.aggregate(
                media=Avg("nota")
            )["media"]
        )

        return render(
            request,
            "perfil_motorista.html",
            {
                "motorista": motorista,
                "avaliacoes": avaliacoes,
                "media_avaliacao":
                    media_avaliacao
            }
        )


class AvaliacaoView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        avaliacoes = (
            Avaliacao.objects
            .select_related(
                "avaliador",
                "motorista"
            )
            .order_by(
                "-id"
            )
        )

        return render(
            request,
            "avaliacoes.html",
            {
                "avaliacoes": avaliacoes
            }
        )


class PaisView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        paises = Pais.objects.all()

        return render(
            request,
            "pais.html",
            {
                "paises": paises
            }
        )


class EstadoView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        estados = Estado.objects.all()

        return render(
            request,
            "estado.html",
            {
                "estados": estados
            }
        )


class CidadeView(
    LoginRequiredMixin,
    View
):

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        cidades = Cidade.objects.all()

        return render(
            request,
            "cidade.html",
            {
                "cidades": cidades
            }
        )