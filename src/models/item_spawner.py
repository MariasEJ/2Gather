import random

from src.config import (
    AUMENTO_VELOCIDADE_POR_NIVEL, INTERVALO_SPAWN_INICIAL,
    INTERVALO_SPAWN_MINIMO, PONTOS_POR_NIVEL_DIFICULDADE,
    REDUCAO_SPAWN_POR_NIVEL, VELOCIDADE_QUEDA_INICIAL, VELOCIDADE_QUEDA_MAXIMA,
)
from src.models.lixeiras import LIXEIRAS
from src.models.falling_item import FallingItem
from src.models.particoes import centro_particao


class ItemSpawner:
    def __init__(self, categorias, rng=None):
        if len(categorias) != 2 or len(set(categorias)) != 2 or any(
            c not in LIXEIRAS or not c.ITENS for c in categorias
        ):
            raise ValueError('A rodada exige duas categorias distintas e válidas')
        self.categorias = tuple(categorias)  # Ordem P1, P2.
        self.rng = rng if rng is not None else random.Random()
        self.timer = 0.0
        self.intervalo = INTERVALO_SPAWN_INICIAL
        self.velocidade_queda = VELOCIDADE_QUEDA_INICIAL

    def gerar(self):
        categoria = self.rng.choice(self.categorias)
        residuo = self.rng.choice(categoria.ITENS)
        dono = self.categorias.index(categoria)
        faixa = self.rng.randrange(dono, dono + 5)
        return FallingItem(centro_particao(faixa), residuo, categoria.ID, self.velocidade_queda)

    def update(self, dt, pontuacao):
        nivel = max(0, int(pontuacao) // PONTOS_POR_NIVEL_DIFICULDADE)
        self.intervalo = max(INTERVALO_SPAWN_MINIMO,
                             INTERVALO_SPAWN_INICIAL - REDUCAO_SPAWN_POR_NIVEL * nivel)
        self.velocidade_queda = min(VELOCIDADE_QUEDA_MAXIMA,
                                    VELOCIDADE_QUEDA_INICIAL + AUMENTO_VELOCIDADE_POR_NIVEL * nivel)
        self.timer += max(0.0, dt)
        novos = []
        while self.timer >= self.intervalo:
            self.timer -= self.intervalo
            novos.append(self.gerar())
        return novos
