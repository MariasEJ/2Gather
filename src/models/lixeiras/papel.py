"""Lixeira de papel e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraPapel(Lixeira):
    ID = 'papel'
    NOME = 'PAPEL'
    IMAGEM = 'imagens/lixeira-rec1-papel.png'
    ITENS = (
        Residuo('papel_jornal', 'Jornal', 'imagens/jornal1.png', tamanho=(76, 56)),
        Residuo('papel_pizza', 'Papelão', 'imagens/caixa-pizza.png', tamanho=(88, 60)),
        Residuo('papel_folha', 'Folha de papel', 'imagens/lixo-papel1.png', tamanho=(54, 64)),
        Residuo('papel_caixa', 'Folha de papel', 'imagens/caixa1.png', tamanho=(74, 66)),
        Residuo('papel_copo', 'Folha de papel', 'imagens/copo-milk.png', tamanho=(44, 64)),
        Residuo('papel_copom', 'Folha de papel', 'imagens/lixo-copoM.png', tamanho=(40, 52)),
    )
