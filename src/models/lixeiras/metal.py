"""Lixeira de metal e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraMetal(Lixeira):
    ID = 'metal'
    NOME = 'METAL'
    IMAGEM = 'imagens/lixeira-reci-metal.png'
    ITENS = (
        Residuo('metal_lata', 'Lata de conserva', 'imagens/lixo-lata2.png', tamanho=(28, 28)),
        Residuo('metal_refri', 'Lata de refrigerante', 'imagens/lata-refri.png', tamanho=(28, 28)),
        Residuo('metal_latinha', 'Lata de bebida', 'imagens/outro-refri-lata.png', tamanho=(28, 28)),
    )
