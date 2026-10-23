"""Lixeira de vidro e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraVidro(Lixeira):
    ID = 'vidro'
    NOME = 'VIDRO'
    IMAGEM = 'imagens/lixeira-reci-vidro.png'
    ITENS = (
        Residuo('vidro_pote', 'Pote de vidro', 'imagens/pote-vidro.png', tamanho=(56, 60)),
        Residuo('vidro_perfume', 'Frasco de perfume', 'imagens/perfume.png', tamanho=(44, 54)),
        Residuo('vidro_esmalte', 'Frasco de esmalte', 'imagens/esmalte.png', tamanho=(36, 42)),
        Residuo('vidro_garrafa', 'Garrafa de vidro', 'imagens/garrafa-vidro1.png', tamanho=(42, 80)),
    )
