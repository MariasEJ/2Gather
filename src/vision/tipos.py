"""Tipos simples compartilhados entre visão e camada de entrada."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class PessoaDetectada:
    cx: float
    cy: float
    tamanho: float
    cor: tuple[int, int, int] | None = None  # HSV, quando disponível
    corpo_completo: bool = True


@dataclass
class QuadroVisao:
    pessoas: list[PessoaDetectada]
    frame_bgr: object | None
    timestamp_ms: int


class StatusJogadores(Enum):
    OK = "ok"
    FALTA_JOGADOR = "falta_jogador"
    CRUZARAM = "cruzaram"
    REPOSICIONANDO = "reposicionando"


@dataclass(frozen=True)
class EstadoJogadores:
    p1_cx: float | None
    p2_cx: float | None
    status: StatusJogadores
    prontos: bool = False
    progresso: float = 0.0
