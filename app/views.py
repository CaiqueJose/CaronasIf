from datetime import time
import time as time_module
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg, Q, Exists, OuterRef
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView, UpdateView
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

from app.forms import CadastroForm, LoginForm, UserProfileForm
from app.permissions import pode_cadastrar_carona

from app.models import (
    Pais,
    Estado,
    Cidade,
    Destino,
    Carona,
    Conversa,
    Mensagem,
    Avaliacao,
    SolicitacaoCNH,
    PerfilUsuario,
    SolicitacaoCarona
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
    

@staff_member_required
def gerenciar_solicitacoes_cnh(request):
    if request.method == "POST":
        solicitacao_id = request.POST.get("solicitacao_id")
        acao = request.POST.get("acao")

        solicitacao = get_object_or_404(
            SolicitacaoCNH,
            pk=solicitacao_id,
            status=SolicitacaoCNH.Status.PENDENTE,
        )

        if acao == "aprovar":
            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=solicitacao.user
            )

            perfil.is_verificado = True
            perfil.save(update_fields=["is_verificado"])

            grupo_motorista, _ = Group.objects.get_or_create(
                name="Motorista"
            )
            solicitacao.user.groups.add(grupo_motorista)

            solicitacao.status = SolicitacaoCNH.Status.APROVADA
            solicitacao.data_decisao = timezone.now()
            solicitacao.save(
                update_fields=["status", "data_decisao"]
            )

            messages.success(
                request,
                f"A solicitação de {solicitacao.user.username} "
                "foi aprovada."
            )

        elif acao == "recusar":
            solicitacao.status = SolicitacaoCNH.Status.REJEITADA
            solicitacao.data_decisao = timezone.now()
            solicitacao.save(
                update_fields=["status", "data_decisao"]
            )

            possui_aprovacao = SolicitacaoCNH.objects.filter(
                user=solicitacao.user,
                status=SolicitacaoCNH.Status.APROVADA,
            ).exclude(pk=solicitacao.pk).exists()

            if not possui_aprovacao:
                perfil, _ = PerfilUsuario.objects.get_or_create(
                    user=solicitacao.user
                )
                perfil.is_verificado = False
                perfil.save(update_fields=["is_verificado"])

                grupo = Group.objects.filter(name="Motorista").first()
                if grupo:
                    solicitacao.user.groups.remove(grupo)

            messages.success(
                request,
                f"A solicitação de {solicitacao.user.username} "
                "foi recusada."
            )

        else:
            messages.error(request, "Ação inválida.")

        return redirect("gerenciar_solicitacoes_cnh")

    solicitacoes = SolicitacaoCNH.objects.filter(
        status=SolicitacaoCNH.Status.PENDENTE
    ).select_related("user").order_by("data_solicitacao")

    return render(
        request,
        "admin_solicitacoes_cnh.html",
        {
            "solicitacoes": solicitacoes,
        }
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
                "origem",
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not pode_cadastrar_carona(request.user):
            messages.error(
                request,
                "Você precisa ter a CNH aprovada para cadastrar caronas."
            )
            return redirect("verificacao_cnh")

        return super().dispatch(request, *args, **kwargs)

    def get(
        self,
        request,
        *args,
        **kwargs
    ):

        cidades = Cidade.objects.all()
        destinos = Destino.objects.all()

        return render(
            request,
            "criar_carona.html",
            {
                "cidades": cidades,
                "destinos": destinos,
            }
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

        if not (origem and destino and data_hora and valor and vagas):
            messages.error(request, "Por favor, preencha todos os campos obrigatórios.")
            return render(
                request,
                "criar_carona.html",
                {
                    "cidades": Cidade.objects.all(),
                    "destinos": Destino.objects.all(),
                }
            )

        Carona.objects.create(
            motorista=request.user,
            origem_id=origem,
            destino_id=destino,
            data_hora=data_hora,
            valor=valor,
            vagas=vagas
        )

        messages.success(request, "Carona cadastrada com sucesso!")

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


class VerificacaoCNHView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args, **kwargs):
        perfil = getattr(request.user, "perfil", None)

        solicitacao = SolicitacaoCNH.objects.filter(
            user=request.user,
            status=SolicitacaoCNH.Status.PENDENTE
        ).first()

        return render(
            request,
            "verificacao_cnh.html",
            {
                "enviado": solicitacao is not None,
                "verificado": getattr(
                    perfil, "is_verificado", False
                ),
                "solicitacao": solicitacao,
                "nome": solicitacao.nome if solicitacao else "",
                "sobrenome": (
                    solicitacao.sobrenome if solicitacao else ""
                ),
                "usuario": (
                    solicitacao.usuario_informado
                    if solicitacao else request.user.username
                ),
                "email": (
                    solicitacao.email_informado
                    if solicitacao else request.user.email
                ),
            }
        )

    def post(self, request, *args, **kwargs):
        perfil = getattr(request.user, "perfil", None)

        if perfil and perfil.is_verificado:
            return render(
                request,
                "verificacao_cnh.html",
                {
                    "enviado": False,
                    "verificado": True,
                    "erro": "Sua conta já está verificada."
                }
            )

        nome = request.POST.get("nome", "").strip()
        sobrenome = request.POST.get("sobrenome", "").strip()
        usuario = request.POST.get("usuario", "").strip()
        email = request.POST.get("email", "").strip()

        if not all([nome, sobrenome, usuario, email]):
            return render(
                request,
                "verificacao_cnh.html",
                {
                    "enviado": False,
                    "verificado": False,
                    "erro": "Preencha todos os campos.",
                    "nome": nome,
                    "sobrenome": sobrenome,
                    "usuario": request.user.username,
                    "email": request.user.email,
                }
            )

        solicitacao_existente = SolicitacaoCNH.objects.filter(
            user=request.user,
            status=SolicitacaoCNH.Status.PENDENTE
        ).first()

        if solicitacao_existente:
            solicitacao = solicitacao_existente
        else:
            solicitacao = SolicitacaoCNH.objects.create(
                user=request.user,
                nome=nome,
                sobrenome=sobrenome,
                usuario_informado=usuario,
                email_informado=email,
            )

        return render(
            request,
            "verificacao_cnh.html",
            {
                "enviado": True,
                "verificado": False,
                "solicitacao": solicitacao,
                "nome": solicitacao.nome,
                "sobrenome": solicitacao.sobrenome,
                "usuario": solicitacao.usuario_informado,
                "email": solicitacao.email_informado,
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
            Conversa.objects.select_related("carona__motorista", "carona__origem", "carona__destino").prefetch_related(
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
                "participantes",
                "carona__origem",
                "carona__destino"
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

        solicitacao = None
        eh_motorista = False
        eh_passageiro = False
        outro_participante = None

        for part in conversa.participantes.all():
            if part.id != request.user.id:
                outro_participante = part
                break

        if conversa.carona:
            eh_motorista = (conversa.carona.motorista_id == request.user.id)
            eh_passageiro = not eh_motorista

            passageiro_alvo = request.user if eh_passageiro else outro_participante

            if passageiro_alvo:
                solicitacao = (
                    SolicitacaoCarona.objects
                    .filter(carona=conversa.carona, passageiro=passageiro_alvo)
                    .order_by("-criado_em")
                    .first()
                )

        return render(
            request,
            "chat.html",
            {
                "conversas": conversas,
                "conversa": conversa,
                "mensagens": mensagens,
                "solicitacao": solicitacao,
                "eh_motorista": eh_motorista,
                "eh_passageiro": eh_passageiro,
                "outro_participante": outro_participante,
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
            Conversa.objects.select_related("carona__motorista"),
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

        solicitacao_data = None
        if conversa.carona:
            eh_motorista = (conversa.carona.motorista_id == request.user.id)
            outro_part = conversa.participantes.exclude(id=request.user.id).first()
            passageiro_alvo = request.user if not eh_motorista else outro_part

            if passageiro_alvo:
                sol = (
                    SolicitacaoCarona.objects
                    .filter(carona=conversa.carona, passageiro=passageiro_alvo)
                    .order_by("-criado_em")
                    .first()
                )
                if sol:
                    solicitacao_data = {
                        "id": sol.id,
                        "status": sol.status,
                        "status_display": sol.get_status_display(),
                        "passageiro": sol.passageiro.username,
                        "passageiro_id": sol.passageiro.id,
                    }

        return JsonResponse(
            {
                "mensagens": dados,
                "solicitacao": solicitacao_data,
                "vagas": conversa.carona.vagas if conversa.carona else None,
                "eh_motorista": (conversa.carona.motorista_id == request.user.id) if conversa.carona else False,
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


class IniciarChatCaronaView(
    LoginRequiredMixin,
    View
):
    login_url = "/login/"

    def get(
        self,
        request,
        carona_id
    ):
        carona = get_object_or_404(
            Carona.objects.select_related("motorista", "origem", "destino"),
            id=carona_id
        )

        if carona.motorista_id == request.user.id:
            messages.info(request, "Você é o motorista desta carona.")
            return redirect("minhas_caronas")

        # Busca conversa existente com esta carona entre os dois usuários
        conversa = (
            Conversa.objects
            .filter(carona=carona)
            .filter(participantes=request.user)
            .filter(participantes=carona.motorista)
            .first()
        )

        if not conversa:
            # Procura se há conversa genérica entre eles para associar a esta carona
            conversa = (
                Conversa.objects
                .filter(participantes=request.user)
                .filter(participantes=carona.motorista)
                .filter(carona__isnull=True)
                .first()
            )
            if conversa:
                conversa.carona = carona
                conversa.save(update_fields=["carona"])
            else:
                conversa = Conversa.objects.create(carona=carona)
                conversa.participantes.add(request.user, carona.motorista)

        return redirect(
            "abrir_chat",
            conversa_id=conversa.id
        )


class SolicitarVagaView(
    LoginRequiredMixin,
    View
):
    login_url = "/login/"

    def post(
        self,
        request,
        conversa_id
    ):
        conversa = get_object_or_404(
            Conversa.objects.select_related("carona__motorista"),
            id=conversa_id
        )

        if not conversa.carona:
            return JsonResponse(
                {"sucesso": False, "erro": "Esta conversa não possui carona associada."},
                status=400
            )

        if not conversa.participantes.filter(id=request.user.id).exists():
            return JsonResponse(
                {"sucesso": False, "erro": "Você não participa desta conversa."},
                status=403
            )

        if conversa.carona.motorista_id == request.user.id:
            return JsonResponse(
                {"sucesso": False, "erro": "O motorista não pode solicitar vaga na própria carona."},
                status=400
            )

        if conversa.carona.vagas <= 0:
            return JsonResponse(
                {"sucesso": False, "erro": "Não há vagas disponíveis nesta carona."},
                status=400
            )

        solicitacao_ativa = (
            SolicitacaoCarona.objects
            .filter(
                carona=conversa.carona,
                passageiro=request.user,
                status__in=[
                    SolicitacaoCarona.Status.PENDENTE,
                    SolicitacaoCarona.Status.ACEITA
                ]
            )
            .first()
        )

        if solicitacao_ativa:
            return JsonResponse({
                "sucesso": True,
                "status": solicitacao_ativa.status,
                "status_display": solicitacao_ativa.get_status_display(),
                "solicitacao_id": solicitacao_ativa.id,
                "mensagem": "Você já possui uma solicitação em andamento ou aceita."
            })

        solicitacao = SolicitacaoCarona.objects.create(
            carona=conversa.carona,
            passageiro=request.user,
            conversa=conversa,
            status=SolicitacaoCarona.Status.PENDENTE
        )

        Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            texto="🚗 Olá! Gostaria de solicitar 1 vaga nesta carona."
        )

        return JsonResponse({
            "sucesso": True,
            "status": "pendente",
            "status_display": "Pendente",
            "solicitacao_id": solicitacao.id,
            "mensagem": "Solicitação enviada com sucesso! Aguardando o motorista aceitar."
        })


class ResponderSolicitacaoView(
    LoginRequiredMixin,
    View
):
    login_url = "/login/"

    def post(
        self,
        request,
        conversa_id,
        solicitacao_id
    ):
        conversa = get_object_or_404(
            Conversa.objects.select_related("carona"),
            id=conversa_id
        )

        solicitacao = get_object_or_404(
            SolicitacaoCarona.objects.select_related("carona", "passageiro"),
            id=solicitacao_id,
            carona=conversa.carona
        )

        if solicitacao.carona.motorista_id != request.user.id:
            return JsonResponse(
                {"sucesso": False, "erro": "Apenas o motorista pode responder à solicitação."},
                status=403
            )

        acao = request.POST.get("acao", "").strip().lower()

        if acao == "aceitar":
            if solicitacao.carona.vagas <= 0:
                return JsonResponse(
                    {"sucesso": False, "erro": "Não há vagas disponíveis para aceitar esta solicitação."},
                    status=400
                )

            if solicitacao.status == SolicitacaoCarona.Status.ACEITA:
                return JsonResponse({
                    "sucesso": True,
                    "status": "aceita",
                    "status_display": "Aceita",
                    "vagas": solicitacao.carona.vagas,
                    "mensagem": "Esta solicitação já foi aceita."
                })

            solicitacao.status = SolicitacaoCarona.Status.ACEITA
            solicitacao.respondido_em = timezone.now()
            solicitacao.save(update_fields=["status", "respondido_em"])

            solicitacao.carona.vagas = max(0, solicitacao.carona.vagas - 1)
            solicitacao.carona.save(update_fields=["vagas"])

            Mensagem.objects.create(
                conversa=conversa,
                remetente=request.user,
                texto=f"✅ Solicitação de {solicitacao.passageiro.username} aceita! Vaga confirmada. Vagas restantes: {solicitacao.carona.vagas}"
            )

            return JsonResponse({
                "sucesso": True,
                "status": "aceita",
                "status_display": "Aceita",
                "vagas": solicitacao.carona.vagas,
                "mensagem": "Solicitação aceita com sucesso!"
            })

        elif acao == "recusar":
            solicitacao.status = SolicitacaoCarona.Status.RECUSADA
            solicitacao.respondido_em = timezone.now()
            solicitacao.save(update_fields=["status", "respondido_em"])

            Mensagem.objects.create(
                conversa=conversa,
                remetente=request.user,
                texto="❌ Solicitação de vaga recusada pelo motorista."
            )

            return JsonResponse({
                "sucesso": True,
                "status": "recusada",
                "status_display": "Recusada",
                "vagas": solicitacao.carona.vagas,
                "mensagem": "Solicitação recusada."
            })

        return JsonResponse(
            {"sucesso": False, "erro": "Ação inválida."},
            status=400
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