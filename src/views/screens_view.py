import pygame

from src.config import (
    COR_PAINEL,
    COR_TEXTO,
    COR_TEXTO_SUAVE,
    LARGURA,
    ALTURA,
)
from src.vision.tipos import StatusJogadores


class ScreensView:
    def __init__(self, tela):
        self.tela = tela
        self.fonte_titulo = pygame.font.Font(None, 64)
        self.fonte = pygame.font.Font(None, 30)
        self.fonte_pequena = pygame.font.Font(None, 24)
        self.botao_iniciar = pygame.Rect(LARGURA // 2 - 145, 310, 290, 54)
        self.botao_regras = pygame.Rect(LARGURA // 2 - 145, 382, 290, 54)
        self.botao_voltar = pygame.Rect(LARGURA // 2 - 145, 455, 290, 50)

    def _texto_centralizado(self, texto, y, fonte, cor=COR_TEXTO):
        superficie = fonte.render(texto, True, cor)
        self.tela.blit(superficie, superficie.get_rect(center=(LARGURA // 2, y)))

    def _painel(self, altura=300):
        painel = pygame.Rect(100, (ALTURA - altura) // 2, LARGURA - 200, altura)
        pygame.draw.rect(self.tela, COR_PAINEL, painel, border_radius=18)
        pygame.draw.rect(self.tela, (54, 68, 93), painel, width=2, border_radius=18)

    def _botao(self, retangulo, texto):
        pygame.draw.rect(self.tela, (60, 92, 138), retangulo, border_radius=12)
        pygame.draw.rect(self.tela, (111, 151, 205), retangulo, width=2, border_radius=12)
        superficie = self.fonte.render(texto, True, COR_TEXTO)
        self.tela.blit(superficie, superficie.get_rect(center=retangulo.center))

    def acao_botao_menu(self, posicao):
        if self.botao_iniciar.collidepoint(posicao):
            return "iniciar"
        if self.botao_regras.collidepoint(posicao):
            return "regras"
        return None

    def clicou_voltar(self, posicao):
        return self.botao_voltar.collidepoint(posicao)

    def desenhar_menu(self):
        self._painel(390)
        self._texto_centralizado("CATCH DUO", 185, self.fonte_titulo)
        self._texto_centralizado(
            "Um jogo cooperativo de captura", 240, self.fonte_pequena, COR_TEXTO_SUAVE
        )
        self._botao(self.botao_iniciar, "Começar jogo")
        self._botao(self.botao_regras, "Ver regras")
        self._texto_centralizado("ou pressione ESPAÇO para começar", 465, self.fonte_pequena, COR_TEXTO_SUAVE)

    def desenhar_regras(self, num_jogadores=2):
        self._painel(470)
        self._texto_centralizado("REGRAS", 105, self.fonte_titulo)
        regras = ["P1 usa A / D e deve pegar bolinhas."]
        if num_jogadores == 2:
            regras.append("P2 usa as setas e deve pegar quadrados.")
        else:
            regras.append("No modo solo, surgem apenas bolinhas.")
        regras.extend(
            (
                "Item do formato certo vale +1 ponto.",
                "Item do formato errado vale -1 ponto.",
                "Cada item perdido apaga uma bolinha de vida.",
                "A partida termina ao perder as 3 vidas.",
                "Também termina ao atingir -5 pontos.",
                "A frequência e a velocidade aumentam com a pontuação.",
            )
        )
        if num_jogadores == 2:
            regras.append("Cooperem: os jogadores não atravessam um ao outro.")
        for indice, regra in enumerate(regras):
            self._texto_centralizado(regra, 155 + indice * 32, self.fonte_pequena)
        self._botao(self.botao_voltar, "Voltar ao menu")

    def desenhar_calibracao(self, num_jogadores, progresso, status=None):
        self._painel(300)
        self._texto_centralizado("PREPARANDO CÂMERA", 195, self.fonte_titulo)
        if num_jogadores == 1:
            instrucao = "Fique diante da câmera com os quadris visíveis."
        else:
            instrucao = "Fiquem um de cada lado da linha central."
        self._texto_centralizado(instrucao, 255, self.fonte_pequena)
        if status == StatusJogadores.FALTA_JOGADOR or (
            num_jogadores == 1 and progresso <= 0.0
        ):
            dica = "Aguardando detectar os quadris dos jogadores."
        elif status == StatusJogadores.REPOSICIONANDO and num_jogadores == 2:
            dica = "Ajustem a posição: um jogador em cada metade da câmera."
        else:
            dica = "Calibrando por um segundo; não é preciso ficar imóvel."
        self._texto_centralizado(dica, 295, self.fonte_pequena, COR_TEXTO_SUAVE)
        barra = pygame.Rect(LARGURA // 2 - 150, 340, 300, 22)
        pygame.draw.rect(self.tela, (65, 73, 91), barra, border_radius=10)
        preenchimento = barra.copy()
        preenchimento.width = round(barra.width * max(0.0, min(1.0, progresso)))
        if preenchimento.width:
            pygame.draw.rect(self.tela, (86, 220, 145), preenchimento, border_radius=10)

    def desenhar_reposicionar(self, status):
        self._painel(250)
        if status == StatusJogadores.CRUZARAM:
            mensagem = "Vocês trocaram de lado. Voltem às posições iniciais."
        else:
            mensagem = "Não consigo ver todos os jogadores. Voltem à câmera."
        self._texto_centralizado("JOGO PAUSADO", 230, self.fonte_titulo)
        self._texto_centralizado(mensagem, 300, self.fonte_pequena)
        self._texto_centralizado("Permaneçam nas posições iniciais por um segundo.", 345, self.fonte_pequena, COR_TEXTO_SUAVE)

    def desenhar_pausa(self):
        self._painel(190)
        self._texto_centralizado("PAUSADO", 260, self.fonte_titulo)
        self._texto_centralizado("P ou ESC para continuar", 320, self.fonte)

    def desenhar_fim(self, pontuacao, itens_perdidos):
        self._painel(250)
        self._texto_centralizado("FIM DE JOGO", 220, self.fonte_titulo)
        self._texto_centralizado(f"Pontuação: {pontuacao}", 280, self.fonte)
        self._texto_centralizado(f"Itens perdidos: {itens_perdidos}", 320, self.fonte_pequena, COR_TEXTO_SUAVE)
        self._texto_centralizado("Pressione R para jogar novamente", 370, self.fonte)
