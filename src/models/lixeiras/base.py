"""Tipos comuns a todas as lixeiras."""

from dataclasses import dataclass

from src.config import CHAO_Y, ALTURA_JOGADOR, LARGURA_JOGADOR, TAMANHO_ITEM
from src.models.particoes import particao_x


@dataclass(frozen=True)
class Residuo:
    """Imagem e área do item em pixels: uma medida ou (largura, altura)."""

    id: str
    nome: str
    imagem: str
    tamanho: int | tuple[int, int] = TAMANHO_ITEM

    def __post_init__(self):
        dimensoes = self.dimensoes
        if (
            not isinstance(dimensoes, tuple)
            or len(dimensoes) != 2
            or any(type(valor) is not int or valor <= 0 for valor in dimensoes)
        ):
            raise ValueError('O tamanho deve ser um inteiro positivo ou (largura, altura) em pixels.')

    @property
    def dimensoes(self):
        return (self.tamanho, self.tamanho) if isinstance(self.tamanho, int) else self.tamanho


class Lixeira:
    ID = None
    NOME = None
    IMAGEM = None
    ITENS = ()

    def __init__(self, nome, x):
        self.nome = nome
        self.x = float(x)
        self.y = CHAO_Y - ALTURA_JOGADOR
        self.largura = LARGURA_JOGADOR
        self.altura = ALTURA_JOGADOR
        self.direcao = 0
        self.alvo_x = None

    @property
    def particao(self):
        return particao_x(self.x)

    def deslocamento(self, dt, velocidade):
        if self.alvo_x is None:
            return self.direcao * velocidade * dt
        diferenca = self.alvo_x - self.x
        passo = max(-velocidade * dt, min(diferenca, velocidade * dt))
        self.direcao = (passo > 0) - (passo < 0)
        return passo

    def retangulo(self):
        """Área lógica da lixeira; não desenha uma forma na tela."""
        return (self.x - self.largura / 2, self.y, self.largura, self.altura)
