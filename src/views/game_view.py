import pygame

from src.config import ALTURA, COR_FUNDO, COR_TEXTO_SUAVE, LARGURA
from src.views.hud_view import HudView
from src.views.screens_view import ScreensView


class GameView:
    def __init__(self, tela):
        self.tela = tela
        self.hud = HudView(tela)
        self.telas = ScreensView(tela)

    def render(self, model):
        self.tela.fill(COR_FUNDO)
        self._desenhar_cenario()

        if model.estado == model.MENU:
            self.telas.desenhar_menu()
        elif model.estado == model.REGRAS:
            self.telas.desenhar_regras()
        else:
            self.desenhar_jogador(model.p1)
            self.desenhar_jogador(model.p2)
            for item in model.itens:
                self.desenhar_item(item)
            self.hud.desenhar(model)
            dica = pygame.font.Font(None, 22).render(
                "P: pausar  •  ESC: pausar", True, COR_TEXTO_SUAVE
            )
            self.tela.blit(dica, dica.get_rect(midbottom=(LARGURA // 2, ALTURA - 12)))
            if model.estado == model.PAUSADO:
                self.telas.desenhar_pausa()
            elif model.estado == model.FIM:
                self.telas.desenhar_fim(model.pontuacao, model.itens_perdidos)

        pygame.display.flip()

    def _desenhar_cenario(self):
        for y in range(130, ALTURA, 80):
            pygame.draw.line(self.tela, (28, 37, 54), (0, y), (LARGURA, y), 1)
        pygame.draw.line(self.tela, (63, 76, 96), (0, ALTURA - 2), (LARGURA, ALTURA - 2), 3)

    def desenhar_jogador(self, jogador):
        x, y, largura, altura = jogador.retangulo()
        pontos = (
            (round(jogador.x), round(y)),
            (round(x), round(y + altura)),
            (round(x + largura), round(y + altura)),
        )
        pygame.draw.polygon(self.tela, jogador.cor, pontos)
        pygame.draw.polygon(self.tela, (245, 248, 252), pontos, width=2)

    def desenhar_item(self, item):
        x, y, largura, altura = item.retangulo()
        if item.tipo == "circulo":
            pygame.draw.circle(
                self.tela,
                item.cor,
                (round(item.x), round(item.y + altura / 2)),
                round(item.tamanho / 2),
            )
        else:
            pygame.draw.rect(
                self.tela,
                item.cor,
                pygame.Rect(round(x), round(y), round(largura), round(altura)),
                border_radius=4,
            )
