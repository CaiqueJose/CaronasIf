
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.utils import timezone

from .models import *


class CaronaInline(admin.TabularInline):
    model = Carona
    extra = 1


class EstadoInline(admin.TabularInline):
    model = Estado
    extra = 1


class CidadeInline(admin.TabularInline):
    model = Cidade
    extra = 1


class DestinoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    inlines = [CaronaInline]


class PaisAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    inlines = [EstadoInline]


class EstadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "pais")
    search_fields = ("nome", "pais__nome")
    list_filter = ("pais",)
    inlines = [CidadeInline]


class CidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "estado")
    search_fields = ("nome", "estado__nome")
    list_filter = ("estado",)


class CaronaAdmin(admin.ModelAdmin):
    list_display = (
        "motorista",
        "origem",
        "destino",
        "data_hora",
        "valor",
        "vagas",
    )
    search_fields = (
        "origem__nome",
        "motorista__username",
        "destino__nome",
    )
    list_filter = ("destino", "data_hora")


class ConversaAdmin(admin.ModelAdmin):
    list_display = ("id", "carona", "criado_em")
    search_fields = ("carona__origem__nome", "carona__destino__nome")
    filter_horizontal = ("participantes",)


class MensagemAdmin(admin.ModelAdmin):
    list_display = ("conversa", "remetente", "texto", "enviado_em")
    search_fields = ("texto", "remetente__username")
    list_filter = ("enviado_em",)


class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("nota", "motorista", "comentario")
    search_fields = ("comentario", "motorista__username")
    list_filter = ("nota", "motorista")


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verificado", "telefone")
    list_filter = ("is_verificado",)
    search_fields = ("user__username", "user__email")


@admin.register(SolicitacaoCNH)
class SolicitacaoCNHAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "nome",
        "sobrenome",
        "email_informado",
        "status",
        "data_solicitacao",
        "data_decisao",
    )
    list_filter = ("status", "data_solicitacao")
    search_fields = (
        "user__username",
        "nome",
        "sobrenome",
        "email_informado",
    )
    readonly_fields = ("data_solicitacao", "data_decisao")
    actions = ("aprovar_solicitacoes", "rejeitar_solicitacoes")

    @admin.action(description="Aprovar solicitações selecionadas")
    def aprovar_solicitacoes(self, request, queryset):
        grupo, _ = Group.objects.get_or_create(name="Motorista")
        total = 0

        for solicitacao in queryset:
            solicitacao.status = SolicitacaoCNH.Status.APROVADA
            solicitacao.data_decisao = timezone.now()
            solicitacao.save(update_fields=["status", "data_decisao"])

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=solicitacao.user
            )
            perfil.is_verificado = True
            perfil.save(update_fields=["is_verificado"])

            solicitacao.user.groups.add(grupo)
            total += 1

        self.message_user(
            request,
            f"{total} solicitação(ões) aprovada(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Rejeitar solicitações selecionadas")
    def rejeitar_solicitacoes(self, request, queryset):
        total = 0

        for solicitacao in queryset:
            solicitacao.status = SolicitacaoCNH.Status.REJEITADA
            solicitacao.data_decisao = timezone.now()
            solicitacao.save(update_fields=["status", "data_decisao"])

            possui_aprovacao = SolicitacaoCNH.objects.filter(
                user=solicitacao.user,
                status=SolicitacaoCNH.Status.APROVADA,
            ).exists()

            if not possui_aprovacao:
                perfil, _ = PerfilUsuario.objects.get_or_create(
                    user=solicitacao.user
                )
                perfil.is_verificado = False
                perfil.save(update_fields=["is_verificado"])

                grupo = Group.objects.filter(name="Motorista").first()
                if grupo:
                    solicitacao.user.groups.remove(grupo)

            total += 1

        self.message_user(
            request,
            f"{total} solicitação(ões) rejeitada(s).",
            level=messages.SUCCESS,
        )

    def save_model(self, request, obj, form, change):
        if obj.status == SolicitacaoCNH.Status.APROVADA:
            if not obj.data_decisao:
                obj.data_decisao = timezone.now()
            perfil, _ = PerfilUsuario.objects.get_or_create(user=obj.user)
            perfil.is_verificado = True
            perfil.save(update_fields=["is_verificado"])
            grupo, _ = Group.objects.get_or_create(name="Motorista")
            obj.user.groups.add(grupo)
        elif obj.status == SolicitacaoCNH.Status.REJEITADA:
            if not obj.data_decisao:
                obj.data_decisao = timezone.now()
            possui_aprovacao = SolicitacaoCNH.objects.filter(
                user=obj.user,
                status=SolicitacaoCNH.Status.APROVADA,
            ).exclude(pk=obj.pk).exists()
            if not possui_aprovacao:
                perfil, _ = PerfilUsuario.objects.get_or_create(user=obj.user)
                perfil.is_verificado = False
                perfil.save(update_fields=["is_verificado"])
                grupo = Group.objects.filter(name="Motorista").first()
                if grupo:
                    obj.user.groups.remove(grupo)
        super().save_model(request, obj, form, change)


@admin.register(SolicitacaoCarona)
class SolicitacaoCaronaAdmin(admin.ModelAdmin):
    list_display = ("id", "carona", "passageiro", "status", "criado_em", "respondido_em")
    list_filter = ("status", "criado_em")
    search_fields = ("passageiro__username", "carona__origem__nome", "carona__destino__nome")


admin.site.register(Destino, DestinoAdmin)
admin.site.register(Carona, CaronaAdmin)
admin.site.register(Conversa, ConversaAdmin)
admin.site.register(Mensagem, MensagemAdmin)
admin.site.register(Avaliacao, AvaliacaoAdmin)
admin.site.register(Pais, PaisAdmin)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Cidade, CidadeAdmin)