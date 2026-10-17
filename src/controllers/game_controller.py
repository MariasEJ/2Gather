"""Loop principal que conecta entrada, Model e View."""

import pygame

from src.config import FPS, LARGURA, ALTURA, TITULO
from src.controllers.input_controller import InputController
from src.models.game_model import GameModel
from src.views.game_view import GameView


class GameController:
    def __init__(self, tela=None):
        self.tela = tela or pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
        self.model = GameModel()
        self.view = GameView(self.tela)
        self.input = InputController(self.view.telas)
        self.clock = pygame.time.Clock()
        self.rodando = True

    def run(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000.0

            for evento in pygame.event.get():
                if self.input.tratar_evento(evento, self.model) is False:
                    self.rodando = False

            if self.model.estado == self.model.JOGANDO:
                self.model.p1.direcao, self.model.p2.direcao = self.input.ler_direcoes()
            else:
                self.model.p1.direcao = 0
                self.model.p2.direcao = 0

            self.model.update(dt)
            self.view.render(self.model)
