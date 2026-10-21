"""Loop principal que conecta entrada, Model e View."""

import logging

import pygame

from src.config import FPS, LARGURA, ALTURA, TITULO
from src.controllers.input_controller import InputController
from src.models.game_model import GameModel
from src.views.game_view import GameView
from src.controllers.input import criar_fonte_entrada
from src.vision.tipos import StatusJogadores
from src import config


logger = logging.getLogger(__name__)


class GameController:
    def __init__(self, tela=None, input_source=None):
        self.tela = tela or pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
        self.model = GameModel()
        self.view = GameView(self.tela)
        self.input = InputController(self.view.telas)
        self.input_source = input_source if input_source is not None else criar_fonte_entrada()
        self.clock = pygame.time.Clock()
        self.rodando = True
        self._agachamento_armado = False
        self._x_armado = True
        self._estado_entrada = self.model.estado

    def run(self):
        logger.info("Estado inicial: %s; entrada=%s", self.model.estado, type(self.input_source).__name__)
        try:
            while self.rodando:
                dt = self.clock.tick(FPS) / 1000.0
                estado_frame = self.model.estado
                placar_anterior = (self.model.pontuacao, self.model.itens_perdidos)

                for evento in pygame.event.get():
                    estado_anterior = self.model.estado
                    if self.input.tratar_evento(evento, self.model) is False:
                        self.rodando = False
                    if (
                        estado_anterior != self.model.CALIBRANDO
                        and self.model.estado == self.model.CALIBRANDO
                    ):
                        logger.info("Calibracao solicitada: aguardando jogadores visiveis")
                        self.input_source.recalibrar()

                if not self.rodando:
                    break
                entrada = self.input_source.ler()
                self._aplicar_entrada(entrada)
                self.model.update(dt)
                if self.model.estado != estado_frame:
                    logger.info("Estado: %s -> %s (rastreamento=%s, pronto=%s)",
                                estado_frame, self.model.estado, entrada.status.value, entrada.prontos)
                if placar_anterior != (self.model.pontuacao, self.model.itens_perdidos):
                    logger.info("Placar: pontos=%d itens_perdidos=%d", self.model.pontuacao, self.model.itens_perdidos)
                self.view.render(self.model, entrada)
        finally:
            self.input_source.fechar()

    def _aplicar_entrada(self, entrada):
        model = self.model
        if model.estado == model.FIM and self._estado_entrada != model.FIM:
            self._agachamento_armado = False
        self._estado_entrada = model.estado
        for indice, jogador in enumerate(model.jogadores, 1):
            jogador.direcao = 0
            jogador.alvo_x = None
            valido = getattr(entrada, f"valido_p{indice}")
            if valido is None:
                valido = entrada.status == StatusJogadores.OK
            if model.estado == model.JOGANDO and valido and entrada.status != StatusJogadores.CRUZARAM:
                jogador.alvo_x = getattr(entrada, f"alvo_p{indice}")
                jogador.direcao = getattr(entrada, f"dir_p{indice}") or 0

        if not entrada.prontos or entrada.status != StatusJogadores.OK:
            self._agachamento_armado = self._x_armado = False
            return
        if not config.USAR_CAMERA:
            return
        if not entrada.amostra_nova:
            return
        if not entrada.agachado_p1 and not entrada.agachado_p2:
            self._agachamento_armado = True
        if not entrada.bracos_x:
            self._x_armado = True
        if entrada.x_confirmado and self._x_armado:
            self._x_armado = False
            if model.estado == model.REGRAS:
                model.voltar_menu()
            else:
                model.mostrar_regras()
            return
        if entrada.agachamento_confirmado and self._agachamento_armado:
            self._agachamento_armado = False
            if model.estado in (model.MENU, model.CALIBRANDO, model.FIM):
                model.iniciar()
