import pygame

from src import config
from src.config import CHAO_Y, LARGURA, ALTURA
from src.views.hud_view import HudView
from src.views.recursos_visuais import RecursosVisuais
from src.views.screens_view import ScreensView
from src.models.fundos import FundoSimples


class GameView:
    def __init__(self, tela, recursos=None):
        self.tela = tela
        self.recursos = recursos or RecursosVisuais()
        self.hud = HudView(tela, self.recursos)
        self.telas = ScreensView(tela, self.recursos)

    def render(self, model, entrada=None):
        fundo = model.fundo
        if model.estado in (model.MENU, model.CALIBRANDO, model.REGRAS):
            fundo = FundoSimples
        self._desenhar_cenario(fundo)
        if model.estado == model.MENU:
            self.telas.desenhar_menu(config.USAR_CAMERA)
        elif model.estado == model.REGRAS:
            self.telas.desenhar_regras(config.USAR_CAMERA)
        elif model.estado == model.CALIBRANDO:
            self.telas.desenhar_calibracao(usando_camera=config.USAR_CAMERA)
        else:
            self.tela.set_clip(pygame.Rect(0, 0, LARGURA, CHAO_Y))
            for jogador in model.jogadores:
                self.desenhar_jogador(jogador)
            for item in model.itens:
                self.desenhar_item(item)
            self.tela.set_clip(None)
            if model.estado == model.FIM:
                self.telas.desenhar_fim(model.pontuacao)
            else:
                self.hud.desenhar(model)
                if model.estado == model.CONTAGEM:
                    self.telas.desenhar_contagem(model.numero_contagem)
        pygame.display.flip()

    def _desenhar_cenario(self, fundo):
        if fundo is None:
            self.tela.fill((36, 43, 55))
        else:
            self.tela.blit(self.recursos.fundo(fundo.IMAGEM, (LARGURA, CHAO_Y)), (0, 0))
        pygame.draw.rect(self.tela, (0, 0, 0), pygame.Rect(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))

    def desenhar_jogador(self, jogador):
        retangulo = pygame.Rect(round(jogador.x - jogador.largura / 2), jogador.y,
                                jogador.largura, jogador.altura)
        classe = type(jogador)
        self.recursos.desenhar(self.tela, classe.IMAGEM, retangulo, 'centro_base')

    def desenhar_item(self, item):
        retangulo = pygame.Rect(round(item.x - item.largura / 2), round(item.y),
                                item.largura, item.altura)
        self.recursos.desenhar(self.tela, item.imagem, retangulo)
