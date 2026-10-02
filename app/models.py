from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Pais(models.Model):
    nome = models.CharField(
        max_length=50,
        verbose_name="Nome do País"
    )

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"

    def __str__(self):
        return self.nome


class Estado(models.Model):
    nome = models.CharField(
        max_length=50,
        verbose_name="Nome do Estado"
    )

    pais = models.ForeignKey(
        Pais,
        on_delete=models.CASCADE,
        verbose_name="País"
    )

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

    def __str__(self):
        return f"{self.nome}, {self.pais}"


class Cidade(models.Model):
    nome = models.CharField(
        max_length=50,
        verbose_name="Nome da Cidade"
    )

    estado = models.ForeignKey(
        Estado,
        on_delete=models.CASCADE,
        verbose_name="Estado"
    )

    class Meta:
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"

    def __str__(self):
        return f"{self.nome}, {self.estado}"


class Carona(models.Model):
    motorista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caronas",
        verbose_name="Motorista"
    )

    origem = models.ForeignKey(
        Cidade,
        on_delete=models.CASCADE,
        related_name="caronas_origem",
        verbose_name="Origem"
    )

    destino = models.ForeignKey(
        Cidade,
        on_delete=models.CASCADE,
        related_name="caronas_destino",
        verbose_name="Destino"
    )

    data_hora = models.DateTimeField(
        verbose_name="Data e Hora da Carona"
    )

    valor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Valor da Carona"
    )

    vagas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Vagas Disponíveis"
    )

    class Meta:
        verbose_name = "Carona"
        verbose_name_plural = "Caronas"
        ordering = ["data_hora"]

    def __str__(self):
        return (
            f"{self.origem} -> {self.destino} "
            f"({self.data_hora.strftime('%d/%m/%Y %H:%M')})"
        )


class Conversa(models.Model):
    carona = models.ForeignKey(
        Carona,
        on_delete=models.CASCADE,
        related_name="conversas",
        null=True,
        blank=True,
        verbose_name="Carona Associada"
    )

    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversas",
        verbose_name="Participantes"
    )

    criado_em = models.DateTimeField(
        default=timezone.now,
        verbose_name="Criado em"
    )

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Conversa #{self.id}"


class Mensagem(models.Model):
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name="Conversa"
    )

    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Remetente"
    )

    texto = models.TextField(
        verbose_name="Texto da Mensagem"
    )

    enviado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Enviado em"
    )

    lida = models.BooleanField(
        default=False,
        verbose_name="Lida"
    )

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["enviado_em"]

    def __str__(self):
        return f"{self.remetente.username}: {self.texto[:20]}"


class Avaliacao(models.Model):
    avaliador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avaliacoes_feitas",
        verbose_name="Avaliador",
        null=True
    )

    motorista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avaliacoes_recebidas",
        verbose_name="Motorista Avaliado"
    )

    nota = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name="Nota da Avaliação",
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0)
        ]
    )

    comentario = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Comentário"
    )

    criado_em = models.DateTimeField(
        default=timezone.now,
        verbose_name="Criado em"
    )

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

    def __str__(self):
        return f"Nota {self.nota} para {self.motorista.username}"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuário"
    )

    is_verificado = models.BooleanField(
        default=False,
        verbose_name="Verificado",
        help_text="Indica se a conta do usuário foi verificada no sistema."
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefone"
    )

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        status = "Verificado" if self.is_verificado else "Não Verificado"
        return f"{self.user.username} - {status}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_ou_salvar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
    else:
        PerfilUsuario.objects.get_or_create(user=instance)
        instance.perfil.save()
