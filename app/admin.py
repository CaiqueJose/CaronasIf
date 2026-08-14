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
    search_fields = ('nome',)
    inlines = [CidadeInline]


class CidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'estado')
    search_fields = ('nome',)


class CaronaAdmin(admin.ModelAdmin):
    list_display = ('dataHora', 'valor', 'vagas', 'origem')
    search_fields = ('origem',)


class ChatAdmin(admin.ModelAdmin):
    list_display = ('mensagem', 'criadoEm')
    search_fields = ('mensagem',)


class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('nota', 'comentario')
    search_fields = ('comentario',)


admin.site.register(Carona, CaronaAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Avaliacao, AvaliacaoAdmin)
admin.site.register(Pais, PaisAdmin)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Cidade, CidadeAdmin)