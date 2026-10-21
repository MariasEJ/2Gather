"""Reconhecimento geométrico de gestos em landmarks do MediaPipe."""

from math import isfinite

from src.config import LIMIAR_AGACHAMENTO, CONFIANCA_GESTOS


def esta_agachado(hip_y, baseline_hip_y, confianca=1.0):
    """Regra do HerPules, aplicada à referência individual em pé."""
    return bool(baseline_hip_y is not None and isfinite(hip_y)
                and 0 <= hip_y <= 1 and confianca >= CONFIANCA_GESTOS
                and hip_y > baseline_hip_y + LIMIAR_AGACHAMENTO)


def detectar_gestos(landmarks, largura, altura, baseline_hip_y=None):
    """O X usa o tronco; o agachamento usa apenas os dois quadris."""
    def visiveis(indices):
        return all(
            isfinite(landmarks[i].x) and isfinite(landmarks[i].y)
            and 0 <= landmarks[i].x <= 1 and 0 <= landmarks[i].y <= 1
            and getattr(landmarks[i], "visibility", 0) >= CONFIANCA_GESTOS
            for i in indices
        )

    def ponto(i):
        return (landmarks[i].x * largura, landmarks[i].y * altura)

    agachado = visiveis((23, 24)) and esta_agachado(
        (landmarks[23].y + landmarks[24].y) / 2, baseline_hip_y
    )

    bracos_x = False
    if visiveis((11, 12, 13, 14, 15, 16, 23, 24)):
        a, b, c, d = (ponto(i) for i in (13, 15, 14, 16))

        def orientacao(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

        cruzam = (orientacao(a, b, c) * orientacao(a, b, d) < 0
                  and orientacao(c, d, a) * orientacao(c, d, b) < 0)
        ombro_y = min(ponto(11)[1], ponto(12)[1])
        quadril_y = max(ponto(23)[1], ponto(24)[1])
        bracos_x = (cruzam and b[1] < a[1] and d[1] < c[1]
                    and ombro_y <= b[1] < quadril_y
                    and ombro_y <= d[1] < quadril_y)
    return agachado, bracos_x
