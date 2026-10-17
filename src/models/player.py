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
        self.alvo_x = None

    def deslocamento(self, dt, velocidade):
        """Calcula o deslocamento respeitando o limite de velocidade."""
        if self.alvo_x is None:
            return self.direcao * velocidade * dt

        diferenca = self.alvo_x - self.x
        passo = max(-velocidade * dt, min(diferenca, velocidade * dt))
        self.direcao = (passo > 0) - (passo < 0)
        return passo

    def retangulo(self):
        """Retorna (x, y, largura, altura) da área de captura."""
        return (
            self.x - self.largura / 2,
            self.y,
            self.largura,
            self.altura,
        )
