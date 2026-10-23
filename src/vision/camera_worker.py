"""Captura contínua e inferência separadas, com um único frame pendente."""

import logging
import threading
import time

from src.config import (
    CAMERA_ALTURA,
    CAMERA_LARGURA,
    CAMERA_MAX_LEITURAS_FALHAS,
    CAMERA_INDICE,
    INTERVALO_LOG_CAMERA,
)
from src.vision.tipos import QuadroVisao


logger = logging.getLogger(__name__)


class CameraIndisponivelError(RuntimeError):
    """A webcam ou o detector de pose não pôde ser inicializado."""


class CameraWorker(threading.Thread):
    def __init__(self, cv2_module=None, detector_factory=None):
        super().__init__(name="catch-duo-camera", daemon=True)
        if cv2_module is None:
            import cv2 as cv2_module
        self.cv2 = cv2_module
        self._lock = threading.Lock()
        self._novo_frame = threading.Condition(self._lock)
        self._parar = threading.Event()
        self._ultimo = None
        self._frame_recente = None
        self._sequencia = 0
        self._captura_thread = None
        self.erro = None
        self._cap = None
        self._detector_factory = detector_factory

    def run(self):
        detector = None
        try:
            # Os objetos MediaPipe são criados e usados apenas nesta thread.
            self._captura_thread = threading.Thread(target=self._capturar, name='2gather-captura', daemon=True)
            self._captura_thread.start()
            # Não carrega modelos se a câmera falhou ou o usuário já encerrou.
            with self._novo_frame:
                self._novo_frame.wait_for(lambda: self._parar.is_set() or self._frame_recente is not None)
                if self._parar.is_set():
                    return
            if self._detector_factory is None:
                from src.vision.pose_detector import PoseDetector
                self._detector_factory = PoseDetector
            detector = self._detector_factory()
            ultima_sequencia = 0
            inicio_log = time.monotonic()
            capturas_log = self._sequencia
            frames_log = descartados = 0
            while not self._parar.is_set():
                with self._novo_frame:
                    self._novo_frame.wait_for(
                        lambda: self._parar.is_set() or self._sequencia > ultima_sequencia,
                    )
                    if self._parar.is_set():
                        break
                    timestamp_ms, frame = self._frame_recente
                    descartados += max(0, self._sequencia - ultima_sequencia - 1)
                    ultima_sequencia = self._sequencia
                inicio_inferencia = time.monotonic()
                pessoas, frame_anotado = detector.detectar_e_desenhar(frame)
                agora = time.monotonic()
                quadro = QuadroVisao(pessoas, frame_anotado, timestamp_ms,
                                    inferencia_ms=(agora - inicio_inferencia) * 1000,
                                    latencia_ms=agora * 1000 - timestamp_ms)
                with self._lock:
                    self._ultimo = quadro
                frames_log += 1
                if agora - inicio_log >= INTERVALO_LOG_CAMERA:
                    capturadas = self._sequencia
                    logger.info("Camera: captura=%.1f FPS inferencia=%.1f FPS tempo=%.1f ms "
                                "idade_pose=%.1f ms descartados=%d jogadores=%d/2",
                                (capturadas - capturas_log) / (agora - inicio_log),
                                frames_log / (agora - inicio_log), quadro.inferencia_ms,
                                quadro.latencia_ms, descartados, len(pessoas))
                    capturas_log, descartados = capturadas, 0
                    inicio_log, frames_log = agora, 0
        except Exception as exc:
            self.erro = f"Falha ao iniciar ou processar a câmera: {exc}"
            logger.exception(self.erro)
        finally:
            self._solicitar_parada()
            try:
                if detector is not None:
                    detector.fechar()
            finally:
                if self._captura_thread is not None:
                    self._captura_thread.join(timeout=2.0)
                logger.info("Camera e detector encerrados")

    def _capturar(self):
        try:
            logger.info("Abrindo camera indice=%d resolucao=%dx%d", CAMERA_INDICE, CAMERA_LARGURA, CAMERA_ALTURA)
            self._cap = self.cv2.VideoCapture(CAMERA_INDICE)
            if not self._cap.isOpened():
                raise CameraIndisponivelError(f"Não foi possível abrir a câmera de índice {CAMERA_INDICE}.")
            self._cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, CAMERA_LARGURA)
            self._cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_ALTURA)
            if not self._cap.set(self.cv2.CAP_PROP_BUFFERSIZE, 1):
                logger.debug('Driver não aceita limitar buffer; captura contínua mantém só o último frame')
            falhas = 0
            ultimo_timestamp = -1
            while not self._parar.is_set():
                ok, frame = self._cap.read()
                if self._parar.is_set():
                    break
                if not ok:
                    falhas += 1
                    if falhas == 1:
                        logger.warning('Camera nao retornou quadro; tentando recuperar a captura')
                    if falhas >= CAMERA_MAX_LEITURAS_FALHAS:
                        raise CameraIndisponivelError('A câmera parou de fornecer quadros.')
                    self._parar.wait(0.01)
                    continue
                if falhas:
                    logger.info('Captura recuperada apos %d falhas', falhas)
                falhas = 0
                if ultimo_timestamp < 0:
                    logger.info('Primeiro quadro recebido: %dx%d', frame.shape[1], frame.shape[0])
                timestamp = max(time.monotonic_ns() // 1_000_000, ultimo_timestamp + 1)
                ultimo_timestamp = timestamp
                frame = self.cv2.flip(frame, 1)
                with self._novo_frame:
                    self._frame_recente = (timestamp, frame)
                    self._sequencia += 1
                    self._novo_frame.notify()
        except Exception as exc:
            self.erro = f'Falha ao capturar a câmera: {exc}'
            logger.exception(self.erro)
            self._solicitar_parada()
        finally:
            if self._cap is not None:
                self._cap.release()

    def ultimo_frame(self):
        """Prévia recente, independente da frequência da inferência."""
        with self._lock:
            return self._frame_recente

    def _solicitar_parada(self):
        self._parar.set()
        with self._novo_frame:
            self._novo_frame.notify_all()

    def ultimo(self):
        with self._lock:
            return self._ultimo

    def parar(self):
        self._solicitar_parada()
        if self.is_alive():
            self.join(timeout=2.0)
            if self.is_alive():
                logger.warning("Captura ainda bloqueada no driver; encerramento solicitado em segundo plano")
