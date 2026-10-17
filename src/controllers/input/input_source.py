"""Contrato comum das fontes de entrada."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.vision.tipos import StatusJogadores


@dataclass(frozen=True)
class EntradaJogadores:
    dir_p1: int | None = None
    dir_p2: int | None = None
    alvo_p1: float | None = None
    alvo_p2: float | None = None
    status: StatusJogadores = StatusJogadores.OK
    prontos: bool = True
    progresso: float = 1.0
    debug: object | None = None


class InputSource(ABC):
    @abstractmethod
    def ler(self) -> EntradaJogadores:
        """Lê o estado atual dos controles."""

    def fechar(self):
        """Libera os recursos da fonte, quando houver."""

    def recalibrar(self):
        """Reinicia o estado de calibração, quando a fonte precisar."""
