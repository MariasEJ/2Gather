"""Detecção e desenho da pose completa com MediaPipe Solutions."""

import logging
import time
from math import isfinite

import cv2
import mediapipe as mp

from src.config import (
    CONFIANCA_CORPO_COMPLETO,
    CONFIANCA_POSE,
    CONFIANCA_QUADRIS,
    INTERVALO_LOG_CAMERA,
    POSE_COMPLEXITY,
)
from src.vision.tipos import PessoaDetectada
from src.vision.gestos import detectar_gestos


_PONTOS_CORPO_COMPLETO = (0, 11, 12, 23, 24, 25, 26, 27, 28)
logger = logging.getLogger(__name__)


class PoseDetector:
    """Retorna centro do corpo e anota o esqueleto completo no frame da câmera."""

    def __init__(self):
        if not hasattr(mp, "solutions"):
            raise RuntimeError("MediaPipe sem Solutions. Instale requirements.txt no ambiente Python 3.12 do projeto.")
        logger.info("MediaPipe %s; poses=%d complexidade=%d confianca=%.2f visibilidade_quadris=%.2f",
                    mp.__version__, 2, POSE_COMPLEXITY, CONFIANCA_POSE, CONFIANCA_QUADRIS)
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self._poses = []
        self._ultimo_log = float("-inf")
        try:
            for _ in range(2):
                self._poses.append(self._criar_pose())
        except Exception:
            self.fechar()
            raise

    @staticmethod
    def _criar_pose():
        return mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=POSE_COMPLEXITY,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=CONFIANCA_POSE,
            min_tracking_confidence=CONFIANCA_POSE,
        )

    def detectar_e_desenhar(self, frame_bgr):
        altura, largura = frame_bgr.shape[:2]
        meio = largura // 2
        regioes = [(0, meio), (meio, largura)]

        frame_anotado = frame_bgr.copy()
        pessoas = []
        diagnosticos = []
        cv2.line(frame_anotado, (largura // 2, 0), (largura // 2, altura), (180, 180, 180), 2)
        for indice, ((x1, x2), pose) in enumerate(zip(regioes, self._poses)):
            regiao = frame_bgr[:, x1:x2]
            rgb = cv2.cvtColor(regiao, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            resultado = pose.process(rgb)
            if resultado.pose_landmarks is None:
                diagnosticos.append(f"regiao {indice + 1}: sem pose; afaste-se e ilumine o corpo")
                continue

            # Desenha todos os landmarks e conexões (cabeça, braços, tronco e pernas).
            regiao_anotada = frame_anotado[:, x1:x2].copy()
            self.mp_drawing.draw_landmarks(
                regiao_anotada,
                resultado.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
            )
            frame_anotado[:, x1:x2] = regiao_anotada
            pessoa = self._extrair_pessoa(
                resultado.pose_landmarks.landmark,
                frame_bgr,
                x1,
                x2 - x1,
                largura,
            )
            quadris = resultado.pose_landmarks.landmark[23:25]
            visibilidade = "/".join(f"{p.visibility:.2f}" for p in quadris)
            if pessoa is not None:
                pessoas.append(pessoa)
                diagnosticos.append(
                    f"regiao {indice + 1}: controle OK x={pessoa.cx:.3f} "
                    f"quadris={visibilidade} corpo_completo={pessoa.corpo_completo}"
                )
                altura_texto = max(24, int(altura * 0.06))
                cv2.putText(
                    frame_anotado,
                    f"Regiao {indice + 1}: quadris OK",
                    (x1 + 12, altura_texto),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (80, 220, 130) if pessoa.corpo_completo else (0, 180, 255),
                    2,
                    cv2.LINE_AA,
                )
            else:
                diagnosticos.append(
                    f"regiao {indice + 1}: pose encontrada, quadris rejeitados "
                    f"(visibilidade={visibilidade}, minimo={CONFIANCA_QUADRIS:.2f}); "
                    "enquadre ambos os quadris"
                )

        agora = time.monotonic()
        if agora - self._ultimo_log >= INTERVALO_LOG_CAMERA:
            logger.info("Deteccao %d/2: %s", len(pessoas), "; ".join(diagnosticos))
            self._ultimo_log = agora

        return pessoas, frame_anotado

    @staticmethod
    def _extrair_pessoa(landmarks, frame_bgr, deslocamento_x, largura_regiao, largura_frame):
        quadril_esq, quadril_dir = landmarks[23], landmarks[24]
        if not all(PoseDetector._ponto_visivel(p, CONFIANCA_QUADRIS)
                   for p in (quadril_esq, quadril_dir)):
            return None

        cx_local = (quadril_esq.x + quadril_dir.x) / 2
        cy = (quadril_esq.y + quadril_dir.y) / 2
        cx = (deslocamento_x + cx_local * largura_regiao) / largura_frame
        tamanho = abs(landmarks[11].x - landmarks[12].x) * largura_regiao / largura_frame
        corpo_completo = all(
            PoseDetector._ponto_visivel(landmarks[indice], CONFIANCA_CORPO_COMPLETO)
            for indice in _PONTOS_CORPO_COMPLETO
        )
        cor = PoseDetector._cor_media_tronco(frame_bgr, cx, cy, tamanho)
        _, bracos_x = detectar_gestos(landmarks, largura_regiao, frame_bgr.shape[0])
        return PessoaDetectada(
            cx=cx,
            cy=cy,
            tamanho=tamanho,
            cor=cor,
            corpo_completo=corpo_completo,
            bracos_x=bracos_x,
            confianca_quadris=min(quadril_esq.visibility, quadril_dir.visibility),
        )

    @staticmethod
    def _ponto_visivel(ponto, confianca):
        return (
            isfinite(ponto.x) and isfinite(ponto.y)
            and 0.0 <= ponto.x <= 1.0 and 0.0 <= ponto.y <= 1.0
            and getattr(ponto, "visibility", 0.0) >= confianca
        )

    @staticmethod
    def _cor_media_tronco(frame_bgr, cx, cy, tamanho):
        altura, largura = frame_bgr.shape[:2]
        raio_x = max(3, int(largura * max(tamanho, 0.02) * 0.25))
        raio_y = max(3, int(altura * max(tamanho, 0.02) * 0.35))
        centro_x, centro_y = int(cx * largura), int(cy * altura)
        x1, x2 = max(0, centro_x - raio_x), min(largura, centro_x + raio_x)
        y1, y2 = max(0, centro_y - raio_y), min(altura, centro_y + raio_y)
        recorte = frame_bgr[y1:y2, x1:x2]
        if recorte.size == 0:
            return None
        hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
        media = hsv.reshape(-1, 3).mean(axis=0)
        return tuple(int(canal) for canal in media)

    def fechar(self):
        for pose in self._poses:
            pose.close()
        self._poses.clear()
