import pygame

from src.config import (
    COR_FUNDO,
    COR_TEXTO,
    COR_VIDA,
    COR_VIDA_VAZIA,
    LARGURA,
    MAX_ITENS_PERDIDOS,
)


class HudView:
    def __init__(self, tela):
        self.tela = tela
        self.fonte_pontos = pygame.font.Font(None, 46)

    def desenhar(self, model):
        pontos = self.fonte_pontos.render(str(model.pontuacao), True, COR_TEXTO)
        self.tela.blit(pontos, pontos.get_rect(midtop=(LARGURA // 2, 20)))

        raio = 13
        espacamento = 36
        primeiro_centro_x = LARGURA - 24 - raio - 2 * espacamento
        centro_y = 34
        for indice in range(MAX_ITENS_PERDIDOS):
            centro_x = primeiro_centro_x + indice * espacamento
            vida_ativa = indice >= model.itens_perdidos
            pygame.draw.circle(
                self.tela,
                COR_VIDA_VAZIA,
                (centro_x, centro_y),
                raio,
            )
            if vida_ativa:
                pygame.draw.circle(self.tela, COR_VIDA, (centro_x, centro_y), raio - 2)
            pygame.draw.circle(self.tela, COR_FUNDO, (centro_x, centro_y), raio, width=2)
