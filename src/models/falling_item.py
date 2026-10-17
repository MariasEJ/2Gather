'''
fazer um desse pra cada tipo de lixerira?

    -itens_vidro
    -itens_papel
    ....
    
'''

from src.config import ALTURA, TAMANHO_ITEM


class FallingItem:
    def __init__(self, x, tipo, cor, velocidade):
        if tipo not in ("circulo", "quadrado"):
            raise ValueError("tipo deve ser 'circulo' ou 'quadrado'")
        self.x = float(x)
        self.y = float(-TAMANHO_ITEM)
        self.tipo = tipo
        self.cor = cor
        self.velocidade = float(velocidade)
        self.tamanho = TAMANHO_ITEM
        self.ativo = True

    def update(self, dt):
        self.y += self.velocidade * dt

    def retangulo(self):
        return (self.x - self.tamanho / 2, self.y, self.tamanho, self.tamanho)

    def saiu_da_tela(self):
        return self.y > ALTURA
