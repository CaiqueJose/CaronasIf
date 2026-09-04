from django.db import models
from django.contrib.auth.models import User

class Destino(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome do Destino")
    
    def __str__(self):
        return str(self.nome)
    
    class Meta:
        verbose_name = "Destino"
        verbose_name_plural = "Destinos"

    

class Carona(models.Model):
    motorista = models.ForeignKey(User, on_delete=models.CASCADE, related_name="caronas", verbose_name="Motorista", null=True, blank=True)
    origem = models.CharField(max_length=99, verbose_name="Origem da Carona")
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, verbose_name="Local do destino", null=True, blank=True)
    dataHora = models.DateTimeField(verbose_name="Data e Hora da Carona")
    valor = models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Valor da Carona")
    vagas = models.IntegerField(verbose_name="Vagas Disponíveis")

    def __str__(self):
        return f"{self.origem} -> {self.destino} ({self.dataHora})"

    class Meta:
        verbose_name = "Carona"
        verbose_name_plural = "Caronas"


class Chat(models.Model):
    mensagem = models.TextField(max_length=99, verbose_name="Mensagem")
    criadoEm = models.DateTimeField(verbose_name="Criado Em")

    def __str__(self):
        return f"{self.mensagem}, {self.criadoEm}"

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"


class Avaliacao(models.Model):
    nota = models.IntegerField(verbose_name="Nota da Avaliação")
    comentario = models.TextField(max_length=99, verbose_name="Comentário da Avaliação")
    motorista = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avaliacoes", verbose_name="Motorista", null=True, blank=True)

    def __str__(self):
        return str(self.nota)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"


class Pais(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome da Pais")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Pais"
        verbose_name_plural = "Paises"


class Estado(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome da Estado")
    pais = models.ForeignKey(Pais, verbose_name="Pais do Estado", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome}, {self.pais}"

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"


class Cidade(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome da Cidade")
    estado = models.ForeignKey(Estado, verbose_name="Estado da Cidade", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome}, {self.estado}"

    class Meta:
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"