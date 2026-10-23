"""Entrada corporal sem alternância automática para teclado."""

import logging
import time
from dataclasses import replace

from src.config import (
    CAMERA_JANELA_NOME, CAMERA_TIMEOUT_INICIAL, CAMERA_TIMEOUT_QUADRO,
    COOLDOWN_PULO, INTERVALO_LOG_CAMERA, CAMERA_DESENHAR_LANDMARKS, CAMERA_MAX_IDADE_POSE,
)
from src.controllers.input.input_source import ConfirmadorGestos, EntradaJogadores, InputSource
from src.vision.camera_worker import CameraWorker
from src.vision.mapeamento import SuavizadorEMA, cx_dupla_para_jogo
from src.vision.player_tracker import PlayerTracker
from src.vision.tipos import EstadoJogadores, StatusJogadores

logger = logging.getLogger(__name__)


class CameraInput(InputSource):
    def __init__(self):
        self.worker = self.cv2 = None
        self._erro_camera = None
        self._janela_aberta = self._fechado = False
        self._inicio = time.monotonic()
        self._ultimo_log = float('-inf')
        self.tracker = PlayerTracker()
        self.suav_p1, self.suav_p2 = SuavizadorEMA(), SuavizadorEMA()
        self.confirmador = ConfirmadorGestos()
        self._ultimo_timestamp = self._ultima_entrada = None
        self._timestamp_janela = None
        self._ultimo_pulo = float('-inf')
        try:
            import cv2
            import mediapipe
            if not hasattr(mediapipe, 'solutions'):
                raise RuntimeError('MediaPipe Solutions indisponível')
            self.cv2 = cv2
            self.cv2.namedWindow(CAMERA_JANELA_NOME, self.cv2.WINDOW_NORMAL)
            self._janela_aberta = True
            self.worker = CameraWorker(cv2_module=self.cv2)
            self.worker.start()
        except Exception as exc:
            self._erro_camera = f'Não foi possível iniciar a câmera: {exc}'
            logger.error(self._erro_camera)
            self.fechar()

    @property
    def erro(self):
        return self._erro_camera or (self.worker.erro if self.worker else None)

    def _neutra(self, quadro, status, aviso):
        self.confirmador.reset()
        self.suav_p1.reset()
        self.suav_p2.reset()
        estado = EstadoJogadores(None, None, status)
        return EntradaJogadores(status=status, prontos=False, progresso=0,
                                valido_p1=False, valido_p2=False,
                                debug=(quadro, estado), aviso=aviso)

    def ler(self):
        quadro = self.worker.ultimo() if self.worker else None
        agora = time.monotonic()
        if not self.erro:
            if quadro is None and agora - self._inicio > CAMERA_TIMEOUT_INICIAL:
                self._erro_camera = 'Tempo esgotado aguardando o primeiro quadro da câmera.'
            elif quadro is not None and agora - quadro.timestamp_ms / 1000 > CAMERA_TIMEOUT_QUADRO:
                self._erro_camera = 'A câmera/inferência deixou de produzir quadros novos.'
        self._atualizar_janela(quadro)
        if self.erro:
            if not self._fechado:
                logger.error(self.erro)
                self.fechar()
            return self._neutra(quadro, StatusJogadores.FALTA_JOGADOR,
                                'Câmera indisponível. Reinicie o programa para reconectar.')
        if quadro is None:
            return self._neutra(None, StatusJogadores.REPOSICIONANDO, 'Aguardando a câmera...')
        if agora - quadro.timestamp_ms / 1000 > CAMERA_MAX_IDADE_POSE:
            return self._neutra(quadro, StatusJogadores.REPOSICIONANDO, 'Aguardando uma pose recente...')
        if self._ultimo_timestamp is not None and quadro.timestamp_ms <= self._ultimo_timestamp:
            return replace(self._ultima_entrada, amostra_nova=False,
                           agachamento_confirmado=False, x_confirmado=False, pulo_confirmado=False)

        self._ultimo_timestamp = quadro.timestamp_ms
        estado = self.tracker.atualizar(quadro.pessoas, quadro.timestamp_ms / 1000)
        alvos = []
        for indice, (cx, suavizador) in enumerate(((estado.p1_cx, self.suav_p1),
                                                  (estado.p2_cx, self.suav_p2)), 1):
            if cx is None:
                suavizador.reset()
                alvos.append(None)
            else:
                alvos.append(suavizador.aplicar(cx_dupla_para_jogo(cx, indice)))
        agachamento, x = self.confirmador.atualizar(
            estado.agachado_p1 and estado.agachado_p2, estado.bracos_x,
            quadro.timestamp_ms / 1000, estado.prontos and estado.status == StatusJogadores.OK,
        )
        tempo_quadro = quadro.timestamp_ms / 1000
        pulo = ((estado.pulou_p1 or estado.pulou_p2)
                and tempo_quadro - self._ultimo_pulo >= COOLDOWN_PULO)
        if pulo:
            self._ultimo_pulo = tempo_quadro
        aviso = ''
        if not estado.prontos:
            aviso = ('Voltem aos seus lados e fiquem em pé, com os quadris visíveis.'
                     if estado.status != StatusJogadores.CRUZARAM
                     else 'Vocês trocaram de lado. Voltem às posições iniciais.')
        self._ultima_entrada = EntradaJogadores(
            alvo_p1=alvos[0], alvo_p2=alvos[1],
            valido_p1=alvos[0] is not None, valido_p2=alvos[1] is not None,
            status=estado.status, prontos=estado.prontos, progresso=estado.progresso,
            debug=(quadro, estado), aviso=aviso,
            agachado_p1=estado.agachado_p1, agachado_p2=estado.agachado_p2,
            bracos_x=estado.bracos_x, agachamento_confirmado=agachamento, x_confirmado=x,
            pulo_confirmado=pulo,
        )
        logger.debug('Quadro=%d centros=(%s, %s) alvos=%s status=%s',
                     quadro.timestamp_ms, estado.p1_cx, estado.p2_cx, alvos, estado.status.value)
        if agora - self._ultimo_log >= INTERVALO_LOG_CAMERA:
            logger.info('Controle: status=%s calibracao=%.0f%% prontos=%s',
                        estado.status.value, estado.progresso * 100, estado.prontos)
            self._ultimo_log = agora
        return self._ultima_entrada

    def fechar(self):
        if self._fechado:
            return
        self._fechado = True
        if self.worker:
            self.worker.parar()
        self._destruir_janela()

    def _atualizar_janela(self, quadro):
        if not self._janela_aberta:
            return
        try:
            previa = self.worker.ultimo_frame() if self.worker and not CAMERA_DESENHAR_LANDMARKS else None
            if previa is None and quadro is not None and quadro.frame_bgr is not None:
                previa = (quadro.timestamp_ms, quadro.frame_bgr)
            if previa is not None and previa[0] != self._timestamp_janela:
                self._timestamp_janela = previa[0]
                frame = previa[1].copy()
                meio = frame.shape[1] // 2
                self.cv2.line(frame, (meio, 0), (meio, frame.shape[0]), (180, 180, 180), 2)
                pessoas = len(quadro.pessoas) if quadro else 0
                self.cv2.putText(frame, f'Controles: {pessoas}/2 | Q: fechar camera',
                                 (12, frame.shape[0] - 18), self.cv2.FONT_HERSHEY_SIMPLEX,
                                 0.6, (255, 255, 255), 2, self.cv2.LINE_AA)
                if self._ultima_entrada is not None and self._ultima_entrada.prontos:
                    pes = sum(ref is not None for ref in self.tracker.referencias_pes)
                    instrucao = (f'Controle pronto | Pes calibrados: {pes}/2 | Pule para informacoes'
                                 if pes else 'Controle pronto | Enquadre os pes em pe para calibrar o pulo')
                else:
                    progresso = self._ultima_entrada.progresso if self._ultima_entrada else 0
                    instrucao = f'Calibracao {progresso:.0%}: fiquem em pe, com quadris e pes visiveis'
                self.cv2.putText(frame, instrucao,
                                 (12, 55), self.cv2.FONT_HERSHEY_SIMPLEX,
                                 0.55, (0, 180, 255), 2, self.cv2.LINE_AA)
                if quadro is not None:
                    idade = max(0, time.monotonic() * 1000 - quadro.timestamp_ms)
                    self.cv2.putText(frame, f'Inferencia: {quadro.inferencia_ms:.0f} ms | Idade pose: {idade:.0f} ms',
                                     (12, frame.shape[0] - 44), self.cv2.FONT_HERSHEY_SIMPLEX,
                                     0.5, (255, 255, 255), 1, self.cv2.LINE_AA)
                self.cv2.imshow(CAMERA_JANELA_NOME, frame)
            tecla = self.cv2.waitKey(1) & 0xFF
            visivel = self.cv2.getWindowProperty(CAMERA_JANELA_NOME, self.cv2.WND_PROP_VISIBLE)
        except self.cv2.error:
            logger.exception('Falha ao atualizar a janela OpenCV')
            tecla, visivel = ord('q'), 0
        if tecla == ord('q') or visivel < 1:
            self._erro_camera = 'Janela da câmera fechada.'
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
        logger.info('Reiniciando calibração: fiquem em pé')
        self.tracker.reset()
        self.suav_p1.reset()
        self.suav_p2.reset()
        self.confirmador.reset()
        self._ultimo_pulo = float('-inf')
        # Uma pose em cache não pode virar a primeira amostra da nova calibração.
        if self._ultima_entrada is not None:
            self._ultima_entrada = self._neutra(None, StatusJogadores.REPOSICIONANDO,
                                               'Fiquem em pé, com os quadris visíveis.')
