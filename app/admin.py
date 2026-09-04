from django.contrib import admin
from .models import *


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


class DestinoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


class CaronaAdmin(admin.ModelAdmin):
    list_display = (
        'motorista',
        'origem',
        'destino',
        'dataHora',
        'valor',
        'vagas',
    )

    search_fields = (
        'origem',
        'motorista__username',
        'destino__nome',
    )

    list_filter = (
        'destino',
        'dataHora',
    )


class ChatAdmin(admin.ModelAdmin):
    list_display = ('mensagem', 'criadoEm')
    search_fields = ('mensagem',)
    list_filter = ('criadoEm',)


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


admin.site.register(Carona, CaronaAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Avaliacao, AvaliacaoAdmin)
admin.site.register(Destino, DestinoAdmin)
admin.site.register(Pais, PaisAdmin)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Cidade, CidadeAdmin)