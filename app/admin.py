from django.contrib import admin
from .models import (
    Pais,
    Estado,
    Cidade,
    Carona,
    Conversa,
    Mensagem,
    Avaliacao,
    PerfilUsuario,
)


class EstadoInline(admin.TabularInline):
    model = Estado
    extra = 1


class CidadeInline(admin.TabularInline):
    model = Cidade
    extra = 1


class PaisAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    inlines = [EstadoInline]


class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pais')
    search_fields = ('nome', 'pais__nome')
    list_filter = ('pais',)
    inlines = [CidadeInline]


class CidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'estado')
    search_fields = ('nome', 'estado__nome')
    list_filter = ('estado',)


class CaronaAdmin(admin.ModelAdmin):
    list_display = (
        'motorista',
        'origem',
        'destino',
        'data_hora',
        'valor',
        'vagas',
    )

    search_fields = (
        'origem__nome',
        'motorista__username',
        'destino__nome',
    )

    list_filter = (
        'destino',
        'data_hora',
    )


class ConversaAdmin(admin.ModelAdmin):
    list_display = ('id', 'carona', 'criado_em')
    search_fields = ('carona__origem__nome', 'carona__destino__nome')
    filter_horizontal = ('participantes',)


class MensagemAdmin(admin.ModelAdmin):
    list_display = ('conversa', 'remetente', 'texto', 'enviado_em')
    search_fields = ('texto', 'remetente__username')
    list_filter = ('enviado_em',)


class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = (
        'nota',
        'motorista',
        'comentario',
    )

    search_fields = (
        'comentario',
        'motorista__username',
    )

    list_filter = (
        'nota',
        'motorista',
    )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verificado", "telefone")
    list_filter = ("is_verificado",)
    search_fields = ("user__username", "user__email")


admin.site.register(Carona, CaronaAdmin)
admin.site.register(Conversa, ConversaAdmin)
admin.site.register(Mensagem, MensagemAdmin)
admin.site.register(Avaliacao, AvaliacaoAdmin)
admin.site.register(Pais, PaisAdmin)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Cidade, CidadeAdmin)