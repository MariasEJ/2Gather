"""Lixeira de vidro e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraVidro(Lixeira):
    ID = 'vidro'
    NOME = 'VIDRO'
    IMAGEM = 'imagens/lixeira-reci-vidro.png'
    ITENS = (
        Residuo('vidro_pote', 'Pote de vidro', 'imagens/pote-vidro.png', tamanho=(64, 64)),
        Residuo('vidro_perfume', 'Frasco de perfume', 'imagens/perfume.png', tamanho=(64, 64)),
        Residuo('vidro_esmalte', 'Frasco de esmalte', 'imagens/esmalte.png', tamanho=(64, 64)),
        Residuo('vidro_garrafa', 'Garrafa de vidro', 'imagens/garrafa-vidro1.png', tamanho=(64, 64)),
        Residuo('vidro_taca', 'Taça de vidro', 'imagens/taca-de-vinho.png', tamanho=(64, 64)),
    )
