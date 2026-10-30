from app.permissions import pode_cadastrar_carona
from app.models import Conversa, Mensagem
from django.db.models import Exists, OuterRef


def contexto_motorista(request):
    """
    Context processor para disponibilizar permissões de motorista e contadores nos templates.
    Retorna 'contexto_motorista', 'pode_cadastrar_carona' e 'conversas_com_mensagens_novas'.
    """
    user = getattr(request, "user", None)
    autorizado = pode_cadastrar_carona(user)

    mensagens_novas = 0
    if user and user.is_authenticated:
        mensagens_novas = (
            Conversa.objects
            .filter(participantes=user)
            .filter(
                Exists(
                    Mensagem.objects.filter(
                        conversa=OuterRef('pk'),
                        lida=False
                    ).exclude(
                        remetente=user
                    )
                )
            )
            .distinct()
            .count()
        )

    return {
        "contexto_motorista": autorizado,
        "pode_cadastrar_carona": autorizado,
        "conversas_com_mensagens_novas": mensagens_novas,
    }
