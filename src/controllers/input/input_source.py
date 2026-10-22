"""Contrato comum das fontes de entrada."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.config import TEMPO_CONFIRMACAO_GESTO
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
    agachado_p1: bool = False
    agachado_p2: bool = False
    bracos_x: bool = False
    agachamento_confirmado: bool = False
    x_confirmado: bool = False
    amostra_nova: bool = True
    valido_p1: bool | None = None
    valido_p2: bool | None = None
    aviso: str = ""
    pulo_confirmado: bool = False


class ConfirmadorGestos:
    """Confirma duração em amostras novas, sem contar frames renderizados."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._inicios = {}
        self._ultimo = None

    def atualizar(self, agachados, bracos_x, agora, valido=True):
        if not valido:
            self._inicios.clear()
            self._ultimo = agora
            return False, False
        if self._ultimo is not None and agora <= self._ultimo:
            return False, False
        self._ultimo = agora
        confirmados = []
        for nome, ativo in (("agachar", agachados), ("x", bracos_x)):
            if not ativo:
                self._inicios.pop(nome, None)
                confirmados.append(False)
            else:
                inicio = self._inicios.setdefault(nome, agora)
                confirmados.append(agora - inicio + 1e-9 >= TEMPO_CONFIRMACAO_GESTO)
        return tuple(confirmados)


class InputSource(ABC):
    @abstractmethod
    def ler(self) -> EntradaJogadores:
        """Lê o estado atual dos controles."""

    def fechar(self):
        """Libera os recursos da fonte, quando houver."""

    def recalibrar(self):
        """Reinicia o estado de calibração, quando a fonte precisar."""
