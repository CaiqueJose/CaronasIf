import json
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin.sites import AdminSite

from app.models import PerfilUsuario, SolicitacaoCNH, Pais, Estado, Cidade, Destino, Carona, Conversa, SolicitacaoCarona, Mensagem
from app.permissions import pode_cadastrar_carona
from app.admin import SolicitacaoCNHAdmin


class ControleAcessoCaronaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.grupo_motorista, _ = Group.objects.get_or_create(name="Motorista")

        # 1. Usuário comum não verificado
        self.user_comum = User.objects.create_user(
            username="usuario_comum",
            email="comum@teste.com",
            password="password123"
        )
        self.user_comum.perfil.is_verificado = False
        self.user_comum.perfil.save()

        # 2. Usuário verificado MAS sem grupo Motorista
        self.user_verificado_sem_grupo = User.objects.create_user(
            username="verificado_sem_grupo",
            email="semgrupo@teste.com",
            password="password123"
        )
        self.user_verificado_sem_grupo.perfil.is_verificado = True
        self.user_verificado_sem_grupo.perfil.save()

        # 3. Usuário motorista aprovado (verificado + no grupo Motorista)
        self.user_motorista = User.objects.create_user(
            username="motorista_aprovado",
            email="motorista@teste.com",
            password="password123"
        )
        self.user_motorista.perfil.is_verificado = True
        self.user_motorista.perfil.save()
        self.user_motorista.groups.add(self.grupo_motorista)

        # 4. Administrador (staff / superuser)
        self.admin = User.objects.create_superuser(
            username="admin_user",
            email="admin@teste.com",
            password="password123"
        )

        # Dados geográficos para testes de formulário/carona
        self.pais = Pais.objects.create(nome="Brasil")
        self.estado = Estado.objects.create(nome="Minas Gerais", pais=self.pais)
        self.cidade = Cidade.objects.create(nome="Muzambinho", estado=self.estado)
        self.destino = Destino.objects.create(nome="Guaxupé")

    def test_cenario_1_usuario_nao_autenticado_tenta_acessar_cadastro(self):
        """1. Usuário não autenticado tenta acessar o cadastro: deve redirecionar para login."""
        response = self.client.get(reverse("criar_carona"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

        # POST não autenticado também deve redirecionar
        data_futura = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response_post = self.client.post(reverse("criar_carona"), {
            "origem": self.cidade.id,
            "destino": self.destino.id,
            "data_hora": data_futura,
            "valor": "20.00",
            "vagas": "3"
        })
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(response_post.url.startswith(reverse("login")))

    def test_cenario_2_usuario_comum_nao_verificado_acessa_sistema(self):
        """2. Usuário comum ainda não verificado acessa o sistema."""
        self.assertFalse(pode_cadastrar_carona(self.user_comum))

        self.client.login(username="usuario_comum", password="password123")
        response = self.client.get(reverse("minhas_caronas"))
        self.assertEqual(response.status_code, 200)

        # Verifica se contexto_motorista é False no contexto
        self.assertFalse(response.context["contexto_motorista"])

        # No HTML, deve exibir 'Verificação de CNH' e NÃO 'Cadastrar Carona'
        content = response.content.decode("utf-8")
        self.assertIn("Verificação de CNH", content)
        self.assertNotIn("Cadastrar Carona", content)

    def test_cenario_3_usuario_verificado_sem_grupo_tenta_cadastrar_carona(self):
        """3. Usuário verificado que não pertence ao grupo Motorista tenta cadastrar uma carona."""
        self.assertFalse(pode_cadastrar_carona(self.user_verificado_sem_grupo))

        self.client.login(username="verificado_sem_grupo", password="password123")
        response = self.client.get(reverse("criar_carona"), follow=True)

        # Deve ser redirecionado para verificacao_cnh com mensagem de aviso
        self.assertRedirects(response, reverse("verificacao_cnh"))
        content = response.content.decode("utf-8")
        self.assertIn("Você precisa ter a CNH aprovada para cadastrar caronas.", content)

        # No menu, não deve exibir Cadastrar Carona
        self.assertNotIn("Cadastrar Carona", content)
        self.assertIn("Verificação de CNH", content)

    def test_cenario_4_usuario_aprovado_motorista_acessa_cadastro(self):
        """4. Usuário com CNH aprovada e grupo Motorista acessa o cadastro."""
        self.assertTrue(pode_cadastrar_carona(self.user_motorista))

        self.client.login(username="motorista_aprovado", password="password123")
        response = self.client.get(reverse("criar_carona"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["contexto_motorista"])

        content = response.content.decode("utf-8")
        self.assertIn("Cadastrar Carona", content)
        self.assertNotIn("Verificação de CNH", content)

    def test_cenario_5_administrador_acessa_cadastro(self):
        """5. Administrador acessa o cadastro."""
        self.assertTrue(pode_cadastrar_carona(self.admin))

        self.client.login(username="admin_user", password="password123")
        response = self.client.get(reverse("criar_carona"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["contexto_motorista"])

        content = response.content.decode("utf-8")
        self.assertIn("Cadastrar Carona", content)
        self.assertNotIn("Verificação de CNH", content)

    def test_cenario_6_aprovacao_cnh_atualiza_perfil_e_adiciona_ao_grupo(self):
        """6. A aprovação de CNH atualiza o perfil e adiciona o usuário ao grupo."""
        solicitacao = SolicitacaoCNH.objects.create(
            user=self.user_comum,
            nome="Usuario",
            sobrenome="Comum",
            usuario_informado="usuario_comum",
            email_informado="comum@teste.com",
            status=SolicitacaoCNH.Status.PENDENTE
        )

        self.client.login(username="admin_user", password="password123")
        response = self.client.post(reverse("gerenciar_solicitacoes_cnh"), {
            "solicitacao_id": solicitacao.id,
            "acao": "aprovar"
        })
        self.assertEqual(response.status_code, 302)

        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoCNH.Status.APROVADA)
        self.assertIsNotNone(solicitacao.data_decisao)

        self.user_comum.refresh_from_db()
        self.user_comum.perfil.refresh_from_db()
        self.assertTrue(self.user_comum.perfil.is_verificado)
        self.assertTrue(self.user_comum.groups.filter(name="Motorista").exists())
        self.assertTrue(pode_cadastrar_carona(self.user_comum))

    def test_cenario_7_apos_aprovacao_menu_atualiza_botoes(self):
        """7. Após a aprovação, o botão Verificação de CNH deixa de aparecer e Cadastrar Carona passa a aparecer."""
        self.client.login(username="usuario_comum", password="password123")

        # Antes da aprovação
        response_antes = self.client.get(reverse("minhas_caronas"))
        content_antes = response_antes.content.decode("utf-8")
        self.assertIn("Verificação de CNH", content_antes)
        self.assertNotIn("Cadastrar Carona", content_antes)

        # Criação de solicitação
        solicitacao = SolicitacaoCNH.objects.create(
            user=self.user_comum,
            nome="Usuario",
            sobrenome="Comum",
            usuario_informado="usuario_comum",
            email_informado="comum@teste.com",
            status=SolicitacaoCNH.Status.PENDENTE
        )

        # Admin aprova solicitação
        admin_client = Client()
        admin_client.login(username="admin_user", password="password123")
        admin_client.post(reverse("gerenciar_solicitacoes_cnh"), {
            "solicitacao_id": solicitacao.id,
            "acao": "aprovar"
        })

        # Após a aprovação
        response_depois = self.client.get(reverse("minhas_caronas"))
        content_depois = response_depois.content.decode("utf-8")
        self.assertNotIn("Verificação de CNH", content_depois)
        self.assertIn("Cadastrar Carona", content_depois)

    def test_cenario_8_demais_itens_do_menu_e_funcionalidades_mantidos(self):
        """8. Os demais itens do menu e as funcionalidades existentes continuam funcionando."""
        self.client.login(username="motorista_aprovado", password="password123")
        response = self.client.get(reverse("minhas_caronas"))
        content = response.content.decode("utf-8")

        self.assertIn("Início", content)
        self.assertIn("Minhas Caronas", content)
        self.assertIn("Mensagens", content)
        self.assertIn("Sair", content)

        # Testa criação de carona pelo motorista aprovado
        data_futura = (timezone.now() + timezone.timedelta(days=2)).isoformat()
        response_criar = self.client.post(reverse("criar_carona"), {
            "origem": self.cidade.id,
            "destino": self.destino.id,
            "data_hora": data_futura,
            "valor": "25.00",
            "vagas": 4
        })
        self.assertEqual(response_criar.status_code, 302)
        self.assertTrue(Carona.objects.filter(motorista=self.user_motorista).exists())

    def test_recusa_solicitacao_cnh(self):
        """Garante que a recusa da solicitação preserva a negação de acesso."""
        solicitacao = SolicitacaoCNH.objects.create(
            user=self.user_comum,
            nome="Usuario",
            sobrenome="Comum",
            usuario_informado="usuario_comum",
            email_informado="comum@teste.com",
            status=SolicitacaoCNH.Status.PENDENTE
        )

        self.client.login(username="admin_user", password="password123")
        response = self.client.post(reverse("gerenciar_solicitacoes_cnh"), {
            "solicitacao_id": solicitacao.id,
            "acao": "recusar"
        })
        self.assertEqual(response.status_code, 302)

        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoCNH.Status.REJEITADA)
        self.assertIsNotNone(solicitacao.data_decisao)

        self.user_comum.refresh_from_db()
        self.user_comum.perfil.refresh_from_db()
        self.assertFalse(self.user_comum.perfil.is_verificado)
        self.assertFalse(self.user_comum.groups.filter(name="Motorista").exists())
        self.assertFalse(pode_cadastrar_carona(self.user_comum))

    def test_tratamento_seguro_usuario_sem_perfil_ou_nulo(self):
        """Verifica tratamento seguro de usuário None, anônimo ou sem perfil."""
        self.assertFalse(pode_cadastrar_carona(None))

        user_sem_perfil = User(username="sem_perfil_db")
        self.assertFalse(pode_cadastrar_carona(user_sem_perfil))

    def test_reutilizacao_conversa_ao_pedir_carona_mesmo_motorista(self):
        """Garante que pedir carona com o mesmo motorista reutiliza a conversa existente e não cria duplicatas."""
        self.client.login(username="usuario_comum", password="password123")

        carona_1 = Carona.objects.create(
            motorista=self.user_motorista,
            origem=self.cidade,
            destino=self.destino,
            data_hora=timezone.now() + timezone.timedelta(days=1),
            valor="20.00",
            vagas=3
        )
        carona_2 = Carona.objects.create(
            motorista=self.user_motorista,
            origem=self.cidade,
            destino=self.destino,
            data_hora=timezone.now() + timezone.timedelta(days=3),
            valor="25.00",
            vagas=2
        )

        # 1. Pede a primeira carona: cria a conversa
        resp1 = self.client.get(reverse("iniciar_chat_carona", kwargs={"carona_id": carona_1.id}))
        self.assertEqual(resp1.status_code, 302)
        conversas_iniciais = Conversa.objects.filter(
            participantes=self.user_comum
        ).filter(
            participantes=self.user_motorista
        )
        self.assertEqual(conversas_iniciais.count(), 1)
        conversa_criada = conversas_iniciais.first()
        self.assertEqual(conversa_criada.carona, carona_1)

        # 2. Pede uma segunda carona com o mesmo motorista: deve REUTILIZAR a mesma conversa
        resp2 = self.client.get(reverse("iniciar_chat_carona", kwargs={"carona_id": carona_2.id}))
        self.assertEqual(resp2.status_code, 302)
        conversas_apos = Conversa.objects.filter(
            participantes=self.user_comum
        ).filter(
            participantes=self.user_motorista
        )
        # Não deve criar uma nova conversa (total continua 1)
        self.assertEqual(conversas_apos.count(), 1)
        conversa_reutilizada = conversas_apos.first()
        self.assertEqual(conversa_reutilizada.id, conversa_criada.id)
        # A carona associada da conversa foi atualizada para a nova carona solicitada
        self.assertEqual(conversa_reutilizada.carona, carona_2)

    def test_excluir_conversas_selecionadas(self):
        """Garante que a exclusão em lote de conversas selecionadas remove do banco somente as do participante autenticado."""
        self.client.login(username="usuario_comum", password="password123")

        conversa1 = Conversa.objects.create()
        conversa1.participantes.add(self.user_comum, self.user_motorista)
        conversa2 = Conversa.objects.create()
        conversa2.participantes.add(self.user_comum, self.admin)

        # Outra conversa da qual o usuário comum NÃO faz parte
        conversa_alheia = Conversa.objects.create()
        conversa_alheia.participantes.add(self.user_motorista, self.admin)

        # Excluir conversa1 e tentar excluir conversa_alheia
        payload = json.dumps({"conversa_ids": [conversa1.id, conversa_alheia.id]})
        response = self.client.post(
            reverse("excluir_conversas"),
            data=payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("sucesso"))
        self.assertEqual(data.get("quantidade"), 1)

        # Conversa 1 excluída
        self.assertFalse(Conversa.objects.filter(id=conversa1.id).exists())
        # Conversa 2 ainda existe
        self.assertTrue(Conversa.objects.filter(id=conversa2.id).exists())
        # Conversa alheia NÃO foi excluída
        self.assertTrue(Conversa.objects.filter(id=conversa_alheia.id).exists())

    def test_recusa_carona_com_e_sem_feedback(self):
        """Garante que a recusa da solicitação pelo motorista salva o feedback opcional e cria a mensagem no chat."""
        carona = Carona.objects.create(
            motorista=self.user_motorista,
            origem=self.cidade,
            destino=self.destino,
            data_hora=timezone.now() + timezone.timedelta(days=1),
            valor="20.00",
            vagas=3
        )
        conversa = Conversa.objects.create(carona=carona)
        conversa.participantes.add(self.user_motorista, self.user_comum)

        solicitacao = SolicitacaoCarona.objects.create(
            carona=carona,
            passageiro=self.user_comum,
            conversa=conversa,
            status=SolicitacaoCarona.Status.PENDENTE
        )

        # 1. Login como motorista e recusa COM feedback
        self.client.login(username="motorista_aprovado", password="password123")
        url = reverse("responder_solicitacao", kwargs={"conversa_id": conversa.id, "solicitacao_id": solicitacao.id})
        resp = self.client.post(url, {
            "acao": "recusar",
            "motivo_recusa": "Porta-malas cheio de encomendas."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("sucesso"))
        self.assertEqual(data.get("status"), "recusada")
        self.assertEqual(data.get("motivo_recusa"), "Porta-malas cheio de encomendas.")

        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoCarona.Status.RECUSADA)
        self.assertEqual(solicitacao.motivo_recusa, "Porta-malas cheio de encomendas.")

        msg = Mensagem.objects.filter(conversa=conversa).order_by("-enviado_em").first()
        self.assertIn("❌ Solicitação de vaga recusada pelo motorista.", msg.texto)
        self.assertIn("Motivo: Porta-malas cheio de encomendas.", msg.texto)

        # 2. Testa recusa SEM feedback (opcional) em outra solicitação
        solicitacao2 = SolicitacaoCarona.objects.create(
            carona=carona,
            passageiro=self.user_comum,
            conversa=conversa,
            status=SolicitacaoCarona.Status.PENDENTE
        )
        url2 = reverse("responder_solicitacao", kwargs={"conversa_id": conversa.id, "solicitacao_id": solicitacao2.id})
        resp2 = self.client.post(url2, {
            "acao": "recusar",
            "motivo_recusa": ""
        })
        self.assertEqual(resp2.status_code, 200)
        solicitacao2.refresh_from_db()
        self.assertEqual(solicitacao2.status, SolicitacaoCarona.Status.RECUSADA)
        self.assertIsNone(solicitacao2.motivo_recusa)

        msg2 = Mensagem.objects.filter(conversa=conversa).order_by("-enviado_em").first()
        self.assertEqual(msg2.texto, "❌ Solicitação de vaga recusada pelo motorista.")

