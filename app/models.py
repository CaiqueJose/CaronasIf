from django.db import models
from django.contrib.auth.models import User



class Carona(models.Model):
    dataHora = models.DateTimeField(verbose_name="Data e Hora da Carona")
    valor = models.DecimalField(decimal_places=2, verbose_name="Valor da Carona")
    vagas = models.IntegerField(verbose_name="Vagas Disponíveis")
    origem = models.CharField(max_length=99, verbose_name="Origem da Carona")
    
    def __str__(self):
        return f"{self.dataHora}, {self.valor}, {self.vagas}, {self.origem}"
    class Meta:
        verbose_name = "Carona"
        verbose_name_plural = "Caronas"
        
class Chat(models.Model):
    mensagem = models.TextField(max_length=99, verbose_name="Mensagem")
    criadoEm = models.DateTimeField(verbose_name="Criado Em")
    
    def __str__(self):
        return f"{self.mensagem}, {self.criadoEm}"
    class Meta:
        verbose_name="Chat"
        verbose_name_plural="Chats"

class Avaliacao(models.Model):
    nota = models.IntegerField(verbose_name="Nota da Avaliação")
    comentario = models.TextField(max_length=99, verbose_name="Comentário da Avaliação")
    
    def __str__(self):
        return self.nota
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
    pais = models.ForeignKey(Pais, verbose_name=_("Pais do Estado"), on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nome}, {self.pais}"
    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

class Cidade(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome da Cidade")
    estado = models.ForeignKey(Estado, verbose_name=_("Estado da Cidade"), on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nome}, {self.estado}"
    class Meta:
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"