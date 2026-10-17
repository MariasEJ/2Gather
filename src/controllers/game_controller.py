"""Loop principal que conecta entrada, Model e View."""

import logging

import pygame

from src.config import FPS, LARGURA, ALTURA, TITULO
from src.controllers.input_controller import InputController
from src.models.game_model import GameModel
from src.views.game_view import GameView
from src.controllers.input.keyboard_input import KeyboardInput
from src.vision.tipos import StatusJogadores


logger = logging.getLogger(__name__)


class GameController:
    def __init__(self, tela=None, input_source=None, num_jogadores=2):
        self.tela = tela or pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
        self.model = GameModel(num_jogadores)
        self.view = GameView(self.tela)
        self.input = InputController(self.view.telas)
        self.input_source = input_source or KeyboardInput(num_jogadores)
        self.clock = pygame.time.Clock()
        self.rodando = True

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
                self._trocar_para_teclado_se_camera_falhar()
                entrada = self.input_source.ler()
                if self._trocar_para_teclado_se_camera_falhar():
                    entrada = self.input_source.ler()
                self._aplicar_entrada(entrada)
                self.model.update(dt)
                if self.model.estado != estado_frame:
                    logger.info("Estado: %s -> %s (rastreamento=%s, pronto=%s)",
                                estado_frame, self.model.estado, entrada.status.value, entrada.prontos)
                if placar_anterior != (self.model.pontuacao, self.model.itens_perdidos):
                    logger.info("Placar: pontos=%d itens_perdidos=%d", self.model.pontuacao, self.model.itens_perdidos)
                self.view.render(self.model, entrada.debug)
        finally:
            self.input_source.fechar()

    def _aplicar_entrada(self, entrada):
        model = self.model
        if model.estado == model.CALIBRANDO:
            if entrada.status == StatusJogadores.OK and entrada.prontos:
                model.iniciar()

        if model.estado == model.PAUSADO_POSICAO:
            if entrada.status == StatusJogadores.OK and entrada.prontos:
                model.retomar_por_posicao()

        if model.estado != model.JOGANDO:
            return
        if entrada.status != StatusJogadores.OK or not entrada.prontos:
            model.pausar_por_posicao()
            return

        if entrada.alvo_p1 is not None:
            model.p1.alvo_x = entrada.alvo_p1
            if model.p2 is not None and entrada.alvo_p2 is not None:
                model.p2.alvo_x = entrada.alvo_p2
        else:
            model.p1.alvo_x = None
            model.p1.direcao = entrada.dir_p1 or 0
            if model.p2 is not None:
                model.p2.alvo_x = None
                model.p2.direcao = entrada.dir_p2 or 0

    def _trocar_para_teclado_se_camera_falhar(self):
        erro = getattr(self.input_source, "erro", None)
        if not erro:
            return False
        logger.warning("%s Usando teclado como alternativa (P1: A/D; P2: setas).", erro)
        self.input_source.fechar()
        self.input_source = KeyboardInput(self.model.num_jogadores)
        return True
