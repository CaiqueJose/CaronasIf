from app.permissions import pode_cadastrar_carona


def contexto_motorista(request):
    """
    Context processor para disponibilizar permissões de motorista nos templates.
    Retorna tanto 'contexto_motorista' quanto 'pode_cadastrar_carona' para máxima compatibilidade.
    """
    user = getattr(request, "user", None)
    autorizado = pode_cadastrar_carona(user)
    return {
        "contexto_motorista": autorizado,
        "pode_cadastrar_carona": autorizado,
    }
