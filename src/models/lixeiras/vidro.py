"""Lixeira de vidro e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraVidro(Lixeira):
    ID = 'vidro'
    NOME = 'VIDRO'
    IMAGEM = 'imagens/lixeira-reci-vidro.png'
    ITENS = (
        Residuo('vidro_pote', 'Pote de vidro', 'imagens/pote-vidro.png', tamanho=(28, 28)),
        Residuo('vidro_garrafa', 'Garrafa de vidro', 'imagens/garrafa-vidro1.png', tamanho=(28, 28)),
    )
