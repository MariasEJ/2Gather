"""Resíduos em queda: imagem para exibição e área lógica para captura."""

from src.config import CHAO_Y
from src.models.particoes import particao_x


class FallingItem:
    def __init__(self, x, residuo, categoria_id, velocidade):
        self.item_id = residuo.id
        self.categoria_id = categoria_id
        self.nome = residuo.nome
        self.imagem = residuo.imagem
        self.tamanho = residuo.tamanho
        self.largura, self.altura = residuo.dimensoes
        self.x = float(x)
        self.y = float(-self.altura)
        self.velocidade = float(velocidade)
        self.ativo = True
        self.y_anterior = self.y

    def update(self, dt):
        self.y_anterior = self.y
        self.y += self.velocidade * dt

    @property
    def particao(self):
        return particao_x(self.x)

    def retangulo(self):
        return (self.x - self.largura / 2, self.y, self.largura, self.altura)

    def toca_jogador(self, jogador):
        """Testa a área ocupada pela imagem entre o quadro anterior e o atual."""
        x, y, largura, altura = jogador.retangulo()
        topo = min(self.y_anterior, self.y)
        base = max(self.y_anterior, self.y) + self.altura
        esquerda = self.x - self.largura / 2
        direita = self.x + self.largura / 2
        return direita >= x and esquerda <= x + largura and base >= y and topo <= y + altura

    def saiu_da_tela(self):
        return self.y > CHAO_Y
