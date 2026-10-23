"""Mapeia posições normalizadas da câmera para coordenadas do jogo."""

from src.config import (
    MARGEM_CENTRAL,
    NUM_PARTICOES,
    SUAVIZACAO_ALPHA,
    ZONA_CAMERA_MAX,
    ZONA_CAMERA_MIN,
)
from src.models.particoes import centro_particao


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def cx_dupla_para_jogo(cx, jogador):
    """Cada metade física controla NUM_PARTICOES-1 faixas do jogo."""
    if jogador == 1:
        minimo, maximo = ZONA_CAMERA_MIN, 0.5 - MARGEM_CENTRAL
        primeira, ultima = 0, NUM_PARTICOES - 2
    else:
        minimo, maximo = 0.5 + MARGEM_CENTRAL, ZONA_CAMERA_MAX
        primeira, ultima = 1, NUM_PARTICOES - 1
    t = clamp((cx - minimo) / (maximo - minimo), 0.0, 1.0)
    return centro_particao(primeira) + t * (centro_particao(ultima) - centro_particao(primeira))


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
