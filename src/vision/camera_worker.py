"""Leitura de webcam e inferência em uma thread de fundo."""

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
        self._parar = threading.Event()
        self._ultimo = None
        self.erro = None
        self._cap = None
        self._detector_factory = detector_factory

    def run(self):
        detector = None
        try:
            # Os objetos MediaPipe são criados e usados apenas nesta thread.
            logger.info("Abrindo camera indice=%d resolucao solicitada=%dx%d", CAMERA_INDICE, CAMERA_LARGURA, CAMERA_ALTURA)
            self._cap = self.cv2.VideoCapture(CAMERA_INDICE)
            if not self._cap.isOpened():
                raise CameraIndisponivelError(f"Não foi possível abrir a câmera de índice {CAMERA_INDICE}.")
            self._cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, CAMERA_LARGURA)
            self._cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_ALTURA)
            if self._detector_factory is None:
                from src.vision.pose_detector import PoseDetector
                self._detector_factory = PoseDetector
            detector = self._detector_factory()
            ultimo_timestamp = -1
            leituras_falhas = 0
            inicio_log = time.monotonic()
            frames_log = 0
            while not self._parar.is_set():
                ok, frame = self._cap.read()
                if not ok:
                    leituras_falhas += 1
                    if leituras_falhas == 1:
                        logger.warning("Camera nao retornou quadro; tentando recuperar a captura")
                    if leituras_falhas >= CAMERA_MAX_LEITURAS_FALHAS:
                        raise CameraIndisponivelError(
                            "A câmera parou de fornecer quadros."
                        )
                    time.sleep(0.01)
                    continue
                if leituras_falhas:
                    logger.info("Captura recuperada apos %d falhas", leituras_falhas)
                leituras_falhas = 0
                if ultimo_timestamp < 0:
                    logger.info("Primeiro quadro recebido: %dx%d", frame.shape[1], frame.shape[0])
                frame = self.cv2.flip(frame, 1)
                timestamp_ms = max(time.monotonic_ns() // 1_000_000, ultimo_timestamp + 1)
                ultimo_timestamp = timestamp_ms
                pessoas, frame_anotado = detector.detectar_e_desenhar(frame)
                quadro = QuadroVisao(pessoas, frame_anotado, timestamp_ms)
                with self._lock:
                    self._ultimo = quadro
                frames_log += 1
                agora = time.monotonic()
                if agora - inicio_log >= INTERVALO_LOG_CAMERA:
                    logger.info("Camera ativa: %.1f FPS de captura/inferencia; jogadores=%d/%d",
                                frames_log / (agora - inicio_log), len(pessoas), 2)
                    inicio_log, frames_log = agora, 0
        except Exception as exc:
            self.erro = f"Falha ao iniciar ou processar a câmera: {exc}"
            logger.exception(self.erro)
        finally:
            try:
                if detector is not None:
                    detector.fechar()
            finally:
                if self._cap is not None:
                    self._cap.release()
                logger.info("Camera e detector encerrados")

    def ultimo(self):
        with self._lock:
            return self._ultimo

    def parar(self):
        self._parar.set()
        if self.is_alive():
            self.join(timeout=2.0)
            if self.is_alive():
                logger.warning("Captura ainda bloqueada no driver; encerramento solicitado em segundo plano")
