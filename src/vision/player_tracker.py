"""Associa deteções às identidades P1/P2 e controla a calibração."""

import logging
from math import hypot

from src.config import (
    MARGEM_CENTRAL,
    MARGEM_CRUZAMENTO,
    PESO_COR,
    PESO_POSICAO,
    PESO_TAMANHO,
    TEMPO_ESTABILIDADE,
    TOLERANCIA_FRAMES,
)
from src.vision.tipos import EstadoJogadores, PessoaDetectada, StatusJogadores


logger = logging.getLogger(__name__)


class PlayerTracker:
    def __init__(self, num_jogadores=2):
        if num_jogadores not in (1, 2):
            raise ValueError("num_jogadores deve ser 1 ou 2")
        self.num_jogadores = num_jogadores
        self.reset()

    def reset(self):
        self.p1 = None
        self.p2 = None
        self.travado = False
        self.frames_sem_gente = 0
        self.inicio_estabilidade = None
        self._ultimo_estado = EstadoJogadores(
            None, None, StatusJogadores.REPOSICIONANDO, False, 0.0
        )

    def atualizar(self, pessoas, agora):
        pessoas = [
            pessoa
            for pessoa in pessoas
            # A pose completa continua sendo desenhada pela câmera, mas o
            # controle e a calibração dependem apenas dos quadris visíveis.
            if pessoa is not None
        ]
        pessoas = sorted(pessoas, key=lambda pessoa: pessoa.tamanho, reverse=True)
        pessoas = pessoas[: self.num_jogadores]

        if len(pessoas) < self.num_jogadores:
            return self._tratar_ausencia()
        self.frames_sem_gente = 0

        if not self.travado:
            return self._tentar_calibracao(pessoas, agora)
        if self.num_jogadores == 1:
            self.p1 = pessoas[0]
            return self._salvar(StatusJogadores.OK, True, 1.0)

        novo_p1, novo_p2 = self._associar_dupla(pessoas)
        self.p1, self.p2 = novo_p1, novo_p2
        if self.p1.cx > self.p2.cx + MARGEM_CRUZAMENTO:
            self.travado = False
            self.inicio_estabilidade = None
            return self._salvar(StatusJogadores.CRUZARAM, False, 0.0)
        return self._salvar(StatusJogadores.OK, True, 1.0)

    def _tratar_ausencia(self):
        self.frames_sem_gente += 1
        if self.frames_sem_gente <= TOLERANCIA_FRAMES:
            anterior = self._ultimo_estado
            if anterior.status == StatusJogadores.OK:
                return anterior
            if self.inicio_estabilidade is not None:
                return self._salvar(StatusJogadores.REPOSICIONANDO, False, anterior.progresso)

        self.travado = False
        self.inicio_estabilidade = None
        return self._salvar(StatusJogadores.FALTA_JOGADOR, False, 0.0)

    def _tentar_calibracao(self, pessoas, agora):
        ordenadas = sorted(pessoas, key=lambda pessoa: pessoa.cx)
        if self.num_jogadores == 1:
            atuais = (ordenadas[0],)
            posicao_inicial_valida = True
        else:
            esquerda, direita = ordenadas
            posicao_inicial_valida = (
                esquerda.cx < 0.5 - MARGEM_CENTRAL
                and direita.cx > 0.5 + MARGEM_CENTRAL
            )
            atuais = (esquerda, direita)

        self.p1 = atuais[0]
        self.p2 = atuais[1] if self.num_jogadores == 2 else None

        if not posicao_inicial_valida:
            self.inicio_estabilidade = None
            return self._salvar(StatusJogadores.REPOSICIONANDO, False, 0.0)

        if self.inicio_estabilidade is None:
            self.inicio_estabilidade = agora
        decorrido = max(0.0, agora - self.inicio_estabilidade)
        progresso = min(1.0, decorrido / TEMPO_ESTABILIDADE)
        if progresso >= 1.0:
            self.p1 = atuais[0]
            self.p2 = atuais[1] if self.num_jogadores == 2 else None
            self.travado = True
            self.inicio_estabilidade = None
            return self._salvar(StatusJogadores.OK, True, 1.0)
        return self._salvar(StatusJogadores.REPOSICIONANDO, False, progresso)

    def _associar_dupla(self, pessoas):
        a, b = pessoas
        custo_direto = self._custo(a, self.p1) + self._custo(b, self.p2)
        custo_trocado = self._custo(a, self.p2) + self._custo(b, self.p1)
        return (a, b) if custo_direto <= custo_trocado else (b, a)

    @staticmethod
    def _custo(atual, anterior):
        custo = PESO_POSICAO * hypot(atual.cx - anterior.cx, atual.cy - anterior.cy)
        custo += PESO_TAMANHO * abs(atual.tamanho - anterior.tamanho)
        if atual.cor is not None and anterior.cor is not None:
            dh = min(abs(atual.cor[0] - anterior.cor[0]), 180 - abs(atual.cor[0] - anterior.cor[0])) / 90
            ds = abs(atual.cor[1] - anterior.cor[1]) / 255
            dv = abs(atual.cor[2] - anterior.cor[2]) / 255
            custo += PESO_COR * hypot(dh, ds, dv)
        return custo

    def _salvar(self, status, prontos, progresso):
        if (status, prontos) != (self._ultimo_estado.status, self._ultimo_estado.prontos):
            logger.info("Rastreamento: %s -> %s; prontos=%s; ausencias=%d",
                        self._ultimo_estado.status.value, status.value, prontos, self.frames_sem_gente)
        self._ultimo_estado = EstadoJogadores(
            self.p1.cx if self.p1 else None,
            self.p2.cx if self.p2 else None,
            status,
            prontos,
            progresso,
        )
        return self._ultimo_estado
