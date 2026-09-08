from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "Cria os grupos e define suas permissões"

    def handle(self, *args, **kwargs):

        passageiro, _ = Group.objects.get_or_create(name="Passageiro")
        motorista, _ = Group.objects.get_or_create(name="Motorista")
        administrador, _ = Group.objects.get_or_create(
            name="Administrador"
        )

        # -------------------------
        # PASSAGEIRO
        # -------------------------

        passageiro.permissions.set([
            Permission.objects.get(
                codename="view_carona"
            ),
            Permission.objects.get(
                codename="view_avaliacao"
            ),
            Permission.objects.get(
                codename="add_avaliacao"
            ),
        ])

        # -------------------------
        # MOTORISTA
        # -------------------------

        motorista.permissions.set([
            Permission.objects.get(
                codename="view_carona"
            ),
            Permission.objects.get(
                codename="add_carona"
            ),
            Permission.objects.get(
                codename="change_carona"
            ),
            Permission.objects.get(
                codename="delete_carona"
            ),
            Permission.objects.get(
                codename="view_avaliacao"
            ),
        ])

        # -------------------------
        # ADMINISTRADOR
        # -------------------------

        administrador.permissions.set(
            Permission.objects.all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Grupos e permissões criados com sucesso!"
            )
        )