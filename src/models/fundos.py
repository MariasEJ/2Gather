"""Fundos escolhidos para cada rodada; cada classe define sua imagem."""


class Fundo:
    ID = None
    NOME = None
    IMAGEM = None


class FundoSimples(Fundo):
    ID = 'simples'
    NOME = 'simples'
    IMAGEM = 'imagens/fundo1-simples.png'  # Troque pela arte do pátio aqui.


class FundoDecorado(Fundo):
    ID = 'Decorado'
    NOME = 'Decorado'
    IMAGEM = 'imagens/fundo1-decorado.png'  # Troque pela arte do pátio aqui.

class FundoPraia(Fundo):
    ID = 'praia'
    NOME = 'praia'
    IMAGEM = 'imagens/fundo-praia1.gif'

FUNDOS = (FundoSimples, FundoDecorado, FundoPraia)
