"""Divisão horizontal compartilhada pelo movimento e pela coleta."""

from src.config import LARGURA, NUM_PARTICOES


def particao_x(x):
    """Índice de 0 a NUM_PARTICOES-1; a borda pertence à faixa da direita."""
    return max(0, min(NUM_PARTICOES - 1, int(x * NUM_PARTICOES / LARGURA)))


def centro_particao(indice):
    return (indice + 0.5) * LARGURA / NUM_PARTICOES
