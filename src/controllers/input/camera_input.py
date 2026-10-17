"""Fonte de entrada por corpo detectado na webcam."""

import logging
import time

from src.config import (
    CAMERA_JANELA_NOME, CAMERA_TIMEOUT_INICIAL, CAMERA_TIMEOUT_QUADRO,
    INTERVALO_LOG_CAMERA,
)
from src.controllers.input.input_source import EntradaJogadores, InputSource
from src.vision.camera_worker import CameraIndisponivelError, CameraWorker
from src.vision.mapeamento import SuavizadorEMA, cx_para_jogo
from src.vision.player_tracker import PlayerTracker
from src.vision.tipos import EstadoJogadores, StatusJogadores


logger = logging.getLogger(__name__)


class CameraInput(InputSource):
    def __init__(self, num_jogadores=2):
        try:
            import cv2 as cv2_module
            import mediapipe 
        except ImportError as exc:
            raise CameraIndisponivelError(
                "Instale as dependências de câmera listadas em requirements.txt."
            ) from exc

        self.num_jogadores = num_jogadores
        self.cv2 = cv2_module
        self._erro_camera = None
        self._janela_aberta = False
        self._fechado = False
        self._inicio = time.monotonic()
        self._ultimo_log = float("-inf")
        try:
            self.cv2.namedWindow(CAMERA_JANELA_NOME, self.cv2.WINDOW_NORMAL)
            self._janela_aberta = True
            self.worker = CameraWorker(num_jogadores, self.cv2)
            self.worker.start()
        except CameraIndisponivelError:
            self._destruir_janela()
            raise
        except Exception as exc:
            if hasattr(self, "worker"):
                self.worker.parar()
            self._destruir_janela()
            raise CameraIndisponivelError(
                f"Não foi possível abrir a janela da câmera: {exc}"
            ) from exc
        self.tracker = PlayerTracker(num_jogadores)
        self.suav_p1 = SuavizadorEMA()
        self.suav_p2 = SuavizadorEMA()
        self._ultimo_timestamp = None
        self._ultima_entrada = None

    @property
    def erro(self):
        return self._erro_camera or self.worker.erro

    def ler(self):
        quadro = self.worker.ultimo()
        agora = time.monotonic()
        if not self.erro:
            if quadro is None and agora - self._inicio > CAMERA_TIMEOUT_INICIAL:
                self._erro_camera = "Tempo esgotado aguardando o primeiro quadro da câmera."
            elif quadro is not None and agora - quadro.timestamp_ms / 1000 > CAMERA_TIMEOUT_QUADRO:
                self._erro_camera = "A câmera/inferência deixou de produzir quadros novos."
        self._atualizar_janela(quadro)
        if self.erro:
            estado = EstadoJogadores(
                None, None, StatusJogadores.FALTA_JOGADOR, False, 0.0
            )
            return EntradaJogadores(
                status=estado.status, prontos=False, debug=(quadro, estado)
            )
        if quadro is None:
            if agora - self._ultimo_log >= INTERVALO_LOG_CAMERA:
                logger.info("Aguardando inicializacao da camera/MediaPipe (%.1fs)", agora - self._inicio)
                self._ultimo_log = agora
            estado = EstadoJogadores(
                None, None, StatusJogadores.REPOSICIONANDO, False, 0.0
            )
            return EntradaJogadores(
                status=estado.status, prontos=False, debug=(None, estado)
            )
        if quadro.timestamp_ms == self._ultimo_timestamp:
            return self._ultima_entrada

        self._ultimo_timestamp = quadro.timestamp_ms
        estado = self.tracker.atualizar(quadro.pessoas, quadro.timestamp_ms / 1000)
        if estado.prontos and (self._ultima_entrada is None or not self._ultima_entrada.prontos):
            self.suav_p1.reset()
            self.suav_p2.reset()
        alvo_p1 = (
            self.suav_p1.aplicar(cx_para_jogo(estado.p1_cx))
            if estado.p1_cx is not None
            else None
        )
        alvo_p2 = (
            self.suav_p2.aplicar(cx_para_jogo(estado.p2_cx))
            if self.num_jogadores == 2 and estado.p2_cx is not None
            else None
        )
        self._ultima_entrada = EntradaJogadores(
            alvo_p1=alvo_p1,
            alvo_p2=alvo_p2,
            status=estado.status,
            prontos=estado.prontos,
            progresso=estado.progresso,
            debug=(quadro, estado),
        )
        logger.debug("Quadro=%d centros=(%s, %s) alvos=(%s, %s) status=%s",
                     quadro.timestamp_ms, estado.p1_cx, estado.p2_cx,
                     alvo_p1, alvo_p2, estado.status.value)
        if agora - self._ultimo_log >= INTERVALO_LOG_CAMERA:
            logger.info("Controle: status=%s calibracao=%.0f%% prontos=%s alvos=(%s, %s)",
                        estado.status.value, estado.progresso * 100, estado.prontos,
                        round(alvo_p1) if alvo_p1 is not None else None,
                        round(alvo_p2) if alvo_p2 is not None else None)
            self._ultimo_log = agora
        return self._ultima_entrada

    def fechar(self):
        if self._fechado:
            return
        self._fechado = True
        self.worker.parar()
        self._destruir_janela()

    def _atualizar_janela(self, quadro):
        if not self._janela_aberta:
            return
        try:
            if quadro is not None and quadro.frame_bgr is not None:
                frame = quadro.frame_bgr.copy()
                completas = sum(p.corpo_completo for p in quadro.pessoas)
                self.cv2.putText(
                    frame, f"Controles: {len(quadro.pessoas)}/{self.num_jogadores} | Q: teclado",
                    (12, frame.shape[0] - 18), self.cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2, self.cv2.LINE_AA,
                )
                if completas < self.num_jogadores:
                    self.cv2.putText(
                        frame,
                        "Quadris visiveis controlam o jogo; corpo inteiro melhora a pose",
                        (12, 55),
                        self.cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 180, 255),
                        2,
                        self.cv2.LINE_AA,
                    )
                self.cv2.imshow(CAMERA_JANELA_NOME, frame)
            tecla = self.cv2.waitKey(1) & 0xFF
            janela_visivel = self.cv2.getWindowProperty(
                CAMERA_JANELA_NOME, self.cv2.WND_PROP_VISIBLE
            )
        except self.cv2.error:
            logger.exception("Falha ao atualizar a janela OpenCV")
            tecla = ord("q")
            janela_visivel = 0

        if tecla == ord("q") or janela_visivel < 1:
            self._erro_camera = "Janela da câmera fechada; usando teclado como alternativa."
            self.fechar()

    def _destruir_janela(self):
        if not self._janela_aberta:
            return
        try:
            self.cv2.destroyWindow(CAMERA_JANELA_NOME)
        except self.cv2.error:
            pass
        self._janela_aberta = False

    def recalibrar(self):
        logger.info("Reiniciando calibracao e suavizacao")
        self.tracker.reset()
        self.suav_p1.reset()
        self.suav_p2.reset()
        self._ultimo_timestamp = None
        self._ultima_entrada = None
