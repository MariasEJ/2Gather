"""Mapeia posições normalizadas da câmera para coordenadas do jogo."""

from src.config import (
    LARGURA,
    LARGURA_JOGADOR,
    SUAVIZACAO_ALPHA,
    ZONA_CAMERA_MAX,
    ZONA_CAMERA_MIN,
)


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def cx_para_jogo(cx, largura_jogo=LARGURA, meia_largura=LARGURA_JOGADOR / 2):
    faixa = ZONA_CAMERA_MAX - ZONA_CAMERA_MIN
    t = clamp((cx - ZONA_CAMERA_MIN) / faixa, 0.0, 1.0)
    return meia_largura + t * (largura_jogo - 2 * meia_largura)


class SuavizadorEMA:
    """Suaviza pequenas oscilações sem remover resposta ao movimento."""

    def __init__(self, alpha=SUAVIZACAO_ALPHA):
        if not 0 < alpha <= 1:
            raise ValueError("alpha deve estar no intervalo (0, 1]")
        self.alpha = alpha
        self.valor = None

    def aplicar(self, valor):
        if self.valor is None:
            self.valor = float(valor)
        else:
            self.valor = self.alpha * valor + (1 - self.alpha) * self.valor
        return self.valor

    def reset(self):
        self.valor = None
