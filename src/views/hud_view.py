import pygame

from src.config import COR_TEXTO, LARGURA, MAX_ITENS_PERDIDOS


class HudView:
    def __init__(self, tela, recursos):
        self.tela = tela
        self.recursos = recursos
        self.fonte_pontos = pygame.font.Font('fontes/Stardew_Valley.ttf', 46)

    def desenhar(self, model):
        faixa_placar = pygame.Rect(LARGURA // 2 - 46, 10, 92, 52)
        pygame.draw.rect(self.tela, (10, 14, 22), faixa_placar, border_radius=9)
        pygame.draw.rect(self.tela, (205, 215, 225), faixa_placar, width=1, border_radius=9)
        pontos = self.fonte_pontos.render(str(model.pontuacao), True, COR_TEXTO)
        self.tela.blit(pontos, pontos.get_rect(center=faixa_placar.center))

        faixa_vidas = pygame.Rect(LARGURA - 170, 10, 156, 48)
        pygame.draw.rect(self.tela, (10, 14, 22), faixa_vidas, border_radius=9)
        pygame.draw.rect(self.tela, (205, 215, 225), faixa_vidas, width=1, border_radius=9)
        vidas = MAX_ITENS_PERDIDOS - model.itens_perdidos
        texto_vidas = pygame.font.Font('fontes/Stardew_Valley.ttf', 27).render(f'Vidas: {vidas}', True, COR_TEXTO)
        self.tela.blit(texto_vidas, texto_vidas.get_rect(center=faixa_vidas.center))
