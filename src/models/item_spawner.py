import random

from src.config import (
    AUMENTO_VELOCIDADE_POR_NIVEL,
    CORES_ITENS,
    INTERVALO_SPAWN_INICIAL,
    INTERVALO_SPAWN_MINIMO,
    LARGURA,
    PONTOS_POR_NIVEL_DIFICULDADE,
    REDUCAO_SPAWN_POR_NIVEL,
    TAMANHO_ITEM,
    VELOCIDADE_QUEDA_INICIAL,
    VELOCIDADE_QUEDA_MAXIMA,
)
from src.models.falling_item import FallingItem


class ItemSpawner:
    def __init__(self):
        self.timer = 0.0
        self.intervalo = INTERVALO_SPAWN_INICIAL
        self.velocidade_queda = VELOCIDADE_QUEDA_INICIAL

    def update(self, dt, pontuacao, num_jogadores=2):
        """Retorna os itens novos deste intervalo de tempo."""
        nivel = max(0, int(pontuacao) // PONTOS_POR_NIVEL_DIFICULDADE)
        self.intervalo = max(
            INTERVALO_SPAWN_MINIMO,
            INTERVALO_SPAWN_INICIAL - REDUCAO_SPAWN_POR_NIVEL * nivel,
        )
        self.velocidade_queda = min(
            VELOCIDADE_QUEDA_MAXIMA,
            VELOCIDADE_QUEDA_INICIAL
            + AUMENTO_VELOCIDADE_POR_NIVEL * nivel,
        )

        self.timer += max(0.0, dt)
        itens_novos = []
        # O while mantém o ritmo de spawn mesmo após uma pausa longa do sistema.
        while self.timer >= self.intervalo:
            self.timer -= self.intervalo
            margem = TAMANHO_ITEM / 2
            x = random.uniform(margem, LARGURA - margem)
            tipos = ("circulo",) if num_jogadores == 1 else ("circulo", "quadrado")
            tipo = random.choice(tipos)
            cor = random.choice(CORES_ITENS)
            itens_novos.append(FallingItem(x, tipo, cor, self.velocidade_queda))
        return itens_novos
