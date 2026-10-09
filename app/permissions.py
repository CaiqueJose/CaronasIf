def pode_cadastrar_carona(user):
    """
    Verifica se o usuário possui permissão para cadastrar caronas.

    Regras:
    1. Usuário autenticado e administrador (is_staff ou is_superuser) -> True
    2. Usuário autenticado com perfil.is_verificado=True e pertencente ao grupo 'Motorista' -> True
    3. Qualquer outro caso (não autenticado, sem perfil, não verificado, sem grupo) -> False
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    perfil = getattr(user, "perfil", None)
    if perfil is None or not getattr(perfil, "is_verificado", False):
        return False

    return user.groups.filter(name="Motorista").exists()
