import pygame

from src.config import CHAO_Y, COR_PAINEL, COR_TEXTO, COR_TEXTO_SUAVE, LARGURA
from src.models.lixeiras import LIXEIRAS


class ScreensView:
    def __init__(self, tela, recursos):
        self.tela = tela
        self.recursos = recursos
        self.fonte_titulo = pygame.font.Font(None, 54)
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_pequena = pygame.font.Font(None, 21)
        self.botao_voltar = pygame.Rect(LARGURA // 2 - 140, CHAO_Y - 70, 280, 46)

    def _texto_centralizado(self, texto, y, fonte, cor=COR_TEXTO, x=None, sombra=False):
        superficie = fonte.render(texto, True, cor)
        destino = superficie.get_rect(center=(LARGURA // 2 if x is None else x, y))
        if sombra:
            self.tela.blit(fonte.render(texto, True, (0, 0, 0)), destino.move(2, 2))
        self.tela.blit(superficie, destino)

    def _painel(self):
        painel = pygame.Rect(40, 20, LARGURA - 80, CHAO_Y - 40)
        pygame.draw.rect(self.tela, COR_PAINEL, painel, border_radius=18)
        pygame.draw.rect(self.tela, (54, 68, 93), painel, width=2, border_radius=18)

    def _botao(self, retangulo, texto):
        pygame.draw.rect(self.tela, (60, 92, 138), retangulo, border_radius=12)
        pygame.draw.rect(self.tela, (111, 151, 205), retangulo, width=2, border_radius=12)
        superficie = self.fonte.render(texto, True, COR_TEXTO)
        self.tela.blit(superficie, superficie.get_rect(center=retangulo.center))

    def clicou_voltar(self, posicao):
        return self.botao_voltar.collidepoint(posicao)

    def desenhar_menu(self, usando_camera=True):
        self.recursos.desenhar(self.tela, 'imagens/logo1.png', pygame.Rect(250, 65, 300, 150))
        inicio, regras = (
            ('agache para começar', 'cruze os braços para regras') if usando_camera
            else ('aperte espaço para iniciar', 'aperte x para regras')
        )
        self._texto_centralizado(inicio, 285, self.fonte)
        self._texto_centralizado(regras, 330, self.fonte_pequena, COR_TEXTO_SUAVE)

    def desenhar_regras(self, usando_camera=True):
        self._painel()
        self._texto_centralizado('CATEGORIAS E CONTROLES', 59, self.fonte_titulo)
        self._desenhar_categorias(168)
        linhas = (
            'A captura exige contato e a mesma faixa. Um acerto vale +1; um erro, -1.',
            'Três resíduos perdidos ou -5 pontos encerram a rodada da dupla.',
            'As lixeiras movem somente para os lados e não se atravessam.',
            'Espaço inicia ou reinicia a rodada.',
            'P1: A/D; P2: setas esquerda/direita. X ou ESC retorna.',
        ) if not usando_camera else (
            'A captura exige contato e a mesma faixa. Um acerto vale +1; um erro, -1.',
            'Três resíduos perdidos ou -5 pontos encerram a rodada da dupla.',
            'Movam o corpo para os lados; as lixeiras não se atravessam.',
            'Agachem juntos para iniciar ou reiniciar. Durante o jogo, não faz nada.',
            'Cruzem os braços para abrir e fechar as regras. ESC ou Voltar também retorna.',
        )
        for indice, linha in enumerate(linhas):
            self._texto_centralizado(linha, CHAO_Y - 210 + indice * 26, self.fonte_pequena)
        self._botao(self.botao_voltar, 'Voltar')

    def _desenhar_categorias(self, y):
        for indice, classe in enumerate(LIXEIRAS):
            x = 112 + indice * 144
            cartao = pygame.Rect(x - 66, y - 36, 132, 112)
            pygame.draw.rect(self.tela, (32, 41, 58), cartao, border_radius=9)
            imagem = pygame.Rect(x - 22, y - 28, 44, 34)
            self.recursos.desenhar(self.tela, classe.IMAGEM, imagem)
            nome = pygame.font.Font(None, 20).render(classe.NOME, True, COR_TEXTO)
            self.tela.blit(nome, nome.get_rect(center=(x, y + 13)))
            fonte = pygame.font.Font(None, 15)
            for linha, item in enumerate(classe.ITENS[:2]):
                texto = fonte.render(item.nome, True, COR_TEXTO_SUAVE)
                self.tela.blit(texto, texto.get_rect(center=(x, y + 35 + linha * 17)))

    def desenhar_calibracao(self, progresso=0.0, status=None, usando_camera=True, aviso=''):
        self.desenhar_menu(usando_camera)

    def desenhar_contagem(self, numero):
        self._texto_centralizado(str(numero), CHAO_Y // 2, pygame.font.Font(None, 144), sombra=True)

    def desenhar_fim(self, pontuacao):
        self._texto_centralizado('GAME OVER', CHAO_Y // 2 - 28, self.fonte_titulo, sombra=True)
        self._texto_centralizado(f'Pontuação: {pontuacao}', CHAO_Y // 2 + 28, self.fonte, sombra=True)
