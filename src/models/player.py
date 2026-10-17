from src.config import ALTURA, ALTURA_JOGADOR, LARGURA_JOGADOR


class Player:
    def __init__(self, nome, x, cor, tipo_alvo):
        self.nome = nome
        self.x = float(x)  # centro horizontal
        self.y = ALTURA - ALTURA_JOGADOR
        self.largura = LARGURA_JOGADOR
        self.altura = ALTURA_JOGADOR
        self.cor = cor
        self.tipo_alvo = tipo_alvo
        self.direcao = 0

    def retangulo(self):
        """Retorna (x, y, largura, altura) da área de captura."""
        return (
            self.x - self.largura / 2,
            self.y,
            self.largura,
            self.altura,
        )
