"""Categorias de lixeiras e os resíduos aceitos por cada uma."""

from src.models.lixeiras.base import Lixeira, Residuo
from src.models.lixeiras.metal import LixeiraMetal
from src.models.lixeiras.organico import LixeiraOrganico
from src.models.lixeiras.papel import LixeiraPapel
from src.models.lixeiras.plastico import LixeiraPlastico
from src.models.lixeiras.vidro import LixeiraVidro

LIXEIRAS = (LixeiraPapel, LixeiraPlastico, LixeiraVidro, LixeiraMetal, LixeiraOrganico)

__all__ = [
    "Lixeira", "Residuo", "LixeiraPapel", "LixeiraPlastico",
    "LixeiraVidro", "LixeiraMetal", "LixeiraOrganico", "LIXEIRAS",
]
