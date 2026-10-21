"""Compatibilidade para imports antigos; categorias vivem em models/lixeiras."""

from src.models.lixeiras import (
    LIXEIRAS, Lixeira, LixeiraMetal, LixeiraOrganico, LixeiraPapel,
    LixeiraPlastico, LixeiraVidro, Residuo,
)

__all__ = [
    "Lixeira", "Residuo", "LixeiraPapel", "LixeiraPlastico",
    "LixeiraVidro", "LixeiraMetal", "LixeiraOrganico", "LIXEIRAS",
]
