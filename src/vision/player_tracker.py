"""Identidades P1/P2, referências individuais dos quadris e recuperação."""

import logging
from dataclasses import replace
from math import fsum, hypot, isfinite

from src.config import (
    AMOSTRAS_CALIBRACAO, CONFIANCA_GESTOS, CONFIANCA_QUADRIS,
    LIMIAR_AGACHAMENTO, MARGEM_CENTRAL, MARGEM_CRUZAMENTO,
    OSCILACAO_CALIBRACAO, PESO_COR, PESO_POSICAO, PESO_TAMANHO,
    TEMPO_ESTABILIDADE, TEMPO_RECUPERACAO_POSE,
)
from src.vision.gestos import DetectorPulo, esta_agachado
from src.vision.tipos import EstadoJogadores, StatusJogadores

logger = logging.getLogger(__name__)


class PlayerTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.p1 = self.p2 = None
        self.referencias = [None, None]
        self.referencias_pes = [None, None]
        self._pulos = [DetectorPulo(), DetectorPulo()]
        self.travado = False
        self._ultimo_tempo = None
        self._ultima_dupla_valida = None
        self._limpar_amostras()
        self._ultimo_estado = EstadoJogadores(None, None, StatusJogadores.REPOSICIONANDO)

    def _limpar_amostras(self):
        self.inicio_estabilidade = None
        self._amostras = [[], []]
        self._amostras_pes = [[], []]

    def atualizar(self, pessoas, agora):
        if self._ultimo_tempo is not None and agora <= self._ultimo_tempo:
            return replace(self._ultimo_estado, pulou_p1=False, pulou_p2=False)
        self._ultimo_tempo = agora
        pessoas = [p for p in pessoas if p is not None
                   and all(isfinite(v) for v in (p.cx, p.cy, p.tamanho, p.confianca_quadris))
                   and 0 <= p.cx <= 1 and 0 <= p.cy <= 1
                   and p.confianca_quadris >= CONFIANCA_QUADRIS]
        pessoas = sorted(pessoas, key=lambda p: p.tamanho, reverse=True)[:2]
        if len(pessoas) < 2:
            self.travado = False
            self._limpar_amostras()
            atuais = [None, None]
            if len(pessoas) == 1 and all(r is not None for r in self.referencias):
                p = pessoas[0]
                custos = [self._custo(p, anterior) for anterior in (self.p1, self.p2)]
                dono = 0 if custos[0] < custos[1] else 1
                lado_correto = p.cx < 0.5 - MARGEM_CENTRAL if dono == 0 else p.cx > 0.5 + MARGEM_CENTRAL
                if lado_correto and min(custos) < 0.35 and abs(custos[0] - custos[1]) > 0.1:
                    atuais[dono] = p
            return self._salvar(StatusJogadores.FALTA_JOGADOR, atuais)

        if all(r is not None for r in self.referencias):
            atuais = self._associar_dupla(pessoas)
            if atuais is None:
                self.travado = False
                self._ultima_dupla_valida = None
                self._limpar_amostras()
                return self._salvar(StatusJogadores.REPOSICIONANDO)
        else:
            atuais = sorted(pessoas, key=lambda p: p.cx)

        if atuais[0].cx > atuais[1].cx + MARGEM_CRUZAMENTO:
            self.travado = False
            self._ultima_dupla_valida = None
            self._limpar_amostras()
            return self._salvar(StatusJogadores.CRUZARAM)

        if not self.travado and self._ultima_dupla_valida is not None:
            # Uma falha breve não deve exigir outras 30 amostras em pé.
            self.travado = (
                agora - self._ultima_dupla_valida <= TEMPO_RECUPERACAO_POSE
                and atuais[0].cx < 0.5 - MARGEM_CENTRAL
                and atuais[1].cx > 0.5 + MARGEM_CENTRAL
                and all(p.confianca_quadris >= CONFIANCA_GESTOS
                        and abs(p.hip_y - ref) <= LIMIAR_AGACHAMENTO
                        for p, ref in zip(atuais, self.referencias))
            )
        if not self.travado:
            return self._calibrar(atuais, agora)
        self.p1, self.p2 = atuais
        self._calibrar_pes(atuais)
        gestos_validos = all(p.confianca_quadris >= CONFIANCA_GESTOS for p in atuais)
        return self._salvar(StatusJogadores.OK, atuais, gestos_validos, 1.0)

    def _calibrar(self, atuais, agora):
        if not (atuais[0].cx < 0.5 - MARGEM_CENTRAL and atuais[1].cx > 0.5 + MARGEM_CENTRAL):
            self._limpar_amostras()
            return self._salvar(StatusJogadores.REPOSICIONANDO)
        for indice, p in enumerate(atuais):
            referencia = self.referencias[indice]
            if p.confianca_quadris < CONFIANCA_GESTOS or (
                referencia is not None and abs(p.hip_y - referencia) > LIMIAR_AGACHAMENTO
            ):
                self._limpar_amostras()
                return self._salvar(StatusJogadores.REPOSICIONANDO)
            amostras = self._amostras[indice]
            if amostras and max(max(amostras), p.hip_y) - min(min(amostras), p.hip_y) > OSCILACAO_CALIBRACAO:
                self._limpar_amostras()
                break
        if self.inicio_estabilidade is None:
            self.inicio_estabilidade = agora
        for indice, p in enumerate(atuais):
            self._amostras[indice].append(p.hip_y)
        progresso = min(1.0, (agora - self.inicio_estabilidade) / TEMPO_ESTABILIDADE,
                        len(self._amostras[0]) / AMOSTRAS_CALIBRACAO)
        if progresso >= 1.0:
            for indice in range(2):
                if self.referencias[indice] is None:
                    self.referencias[indice] = fsum(self._amostras[indice]) / len(self._amostras[indice])
            self.p1, self.p2 = atuais
            self.travado = True
            self._calibrar_pes(atuais)
            self._limpar_amostras()
            return self._salvar(StatusJogadores.OK, atuais, True, 1.0)
        self._calibrar_pes(atuais)
        return self._salvar(StatusJogadores.REPOSICIONANDO, progresso=progresso)

    def _calibrar_pes(self, atuais):
        # Pés fora do enquadramento não bloqueiam o movimento nem o agachamento.
        for indice, pessoa in enumerate(atuais):
            if self.referencias_pes[indice] is not None:
                continue
            amostras = self._amostras_pes[indice]
            referencia = self.referencias[indice]
            if (pessoa.foot_y is None or not isfinite(pessoa.foot_y)
                    or not 0 <= pessoa.foot_y <= 1
                    or pessoa.confianca_quadris < CONFIANCA_GESTOS
                    or (referencia is not None
                        and abs(pessoa.hip_y - referencia) > OSCILACAO_CALIBRACAO)):
                amostras.clear()
                continue
            if amostras and max(*amostras, pessoa.foot_y) - min(*amostras, pessoa.foot_y) > OSCILACAO_CALIBRACAO:
                amostras.clear()
            amostras.append(pessoa.foot_y)
            if len(amostras) > AMOSTRAS_CALIBRACAO:
                amostras.pop(0)
            if referencia is not None and len(amostras) >= AMOSTRAS_CALIBRACAO:
                self.referencias_pes[indice] = fsum(amostras) / len(amostras)
                amostras.clear()

    def _associar_dupla(self, pessoas):
        a, b = pessoas
        direto = self._custo(a, self.p1) + self._custo(b, self.p2)
        trocado = self._custo(a, self.p2) + self._custo(b, self.p1)
        if abs(direto - trocado) < 0.05 or min(direto, trocado) > 1.0:
            return None
        return (a, b) if direto < trocado else (b, a)

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

    def _salvar(self, status, atuais=(None, None), prontos=False, progresso=0.0):
        p1, p2 = atuais
        pulos = [False, False]
        for indice, (detector, pessoa) in enumerate(zip(self._pulos, atuais)):
            if not prontos or pessoa is None:
                detector.reset_movimento()
            else:
                pulos[indice] = detector.atualizar(
                    pessoa.hip_y, pessoa.foot_y, self.referencias[indice],
                    self.referencias_pes[indice], self._ultimo_tempo, pessoa.confianca_quadris,
                )
        if prontos:
            self._ultima_dupla_valida = self._ultimo_tempo
        if (status, prontos) != (self._ultimo_estado.status, self._ultimo_estado.prontos):
            logger.info('Rastreamento: %s -> %s; prontos=%s', self._ultimo_estado.status.value, status.value, prontos)
        self._ultimo_estado = EstadoJogadores(
            p1.cx if p1 else None, p2.cx if p2 else None, status, prontos, progresso,
            bool(prontos and esta_agachado(p1.hip_y, self.referencias[0], p1.confianca_quadris)),
            bool(prontos and esta_agachado(p2.hip_y, self.referencias[1], p2.confianca_quadris)),
            bool(prontos and (p1.bracos_x or p2.bracos_x)),
            pulou_p1=pulos[0], pulou_p2=pulos[1],
        )
        return self._ultimo_estado
