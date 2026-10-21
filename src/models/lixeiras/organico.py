"""Lixeira de resíduos orgânicos e itens aceitos nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraOrganico(Lixeira):
    ID = 'organico'
    NOME = 'ORGÂNICO'
    IMAGEM = 'imagens/lixeira1.png'
    ITENS = (
        Residuo('organico_banana', 'Casca de banana', 'imagens/casca-banana1.png', tamanho=(28, 28)),
        Residuo('organico_maca', 'Resto de maçã', 'imagens/lixo-maca1.png', tamanho=(28, 28)),
        Residuo('organico_comida', 'Resto de comida', 'imagens/lixo-hamburg.png', tamanho=(28, 28)),
        Residuo('organico_coquinho', 'coquinho', 'imagens/coquinho.png', tamanho=(28, 28)),
        Residuo('organico_patoleh', 'patoleh', 'imagens/patoleh.png', tamanho=(28, 28)),
        Residuo('organico_picoleh', 'picoleh', 'imagens/picoleh.png', tamanho=(28, 28)),
    )
