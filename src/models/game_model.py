from src.config import (
    COR_P1,
    COR_P2,
    LARGURA,
    LARGURA_JOGADOR,
    MAX_ITENS_PERDIDOS,
    PONTOS_ACERTO,
    PONTOS_ERRO,
    PONTUACAO_LIMITE_INFERIOR,
    PONTUACAO_MINIMA,
    VELOCIDADE_JOGADOR,
    VELOCIDADE_JOGADOR_CAMERA,
)
from src.models.item_spawner import ItemSpawner
from src.models.player import Player


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def colide(retangulo_a, retangulo_b):
    ax, ay, aw, ah = retangulo_a
    bx, by, bw, bh = retangulo_b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


class GameModel:
    MENU = "MENU"
    REGRAS = "REGRAS"
    CALIBRANDO = "CALIBRANDO"
    JOGANDO = "JOGANDO"
    PAUSADO = "PAUSADO"
    PAUSADO_POSICAO = "PAUSADO_POSICAO"
    FIM = "FIM"

    def __init__(self, num_jogadores=2):
        if num_jogadores not in (1, 2):
            raise ValueError("num_jogadores deve ser 1 ou 2")
        self.num_jogadores = num_jogadores
        self.reset()

    def reset(self):
        self.p1 = Player("P1", LARGURA * 0.25, COR_P1, "circulo")
        self.p2 = (
            Player("P2", LARGURA * 0.75, COR_P2, "quadrado")
            if self.num_jogadores == 2
            else None
        )
        self.itens = []
        self.spawner = ItemSpawner()
        self.pontuacao = 0
        self.itens_perdidos = 0
        self.estado = self.MENU

    def iniciar(self):
        if self.estado in (self.MENU, self.REGRAS, self.CALIBRANDO):
            self.estado = self.JOGANDO

    def iniciar_calibracao(self):
        if self.estado in (self.MENU, self.REGRAS):
            self.estado = self.CALIBRANDO

    def pausar_por_posicao(self):
        if self.estado == self.JOGANDO:
            self.estado = self.PAUSADO_POSICAO

    def retomar_por_posicao(self):
        if self.estado == self.PAUSADO_POSICAO:
            self.estado = self.JOGANDO

    def mostrar_regras(self):
        if self.estado == self.MENU:
            self.estado = self.REGRAS

    def voltar_menu(self):
        if self.estado == self.REGRAS:
            self.estado = self.MENU

    def pausar(self):
        if self.estado == self.JOGANDO:
            self.estado = self.PAUSADO

    def alternar_pausa(self):
        if self.estado == self.JOGANDO:
            self.estado = self.PAUSADO
        elif self.estado == self.PAUSADO:
            self.estado = self.JOGANDO

    def update(self, dt):
        if self.estado != self.JOGANDO:
            return

        dt = max(0.0, float(dt))
        self.mover_jogadores(dt)
        self.itens.extend(
            self.spawner.update(dt, self.pontuacao, self.num_jogadores)
        )
        for item in self.itens:
            item.update(dt)
        self.verificar_capturas()
        if self.estado == self.FIM:
            return
        self._contar_itens_perdidos()
        if (
            self.itens_perdidos >= MAX_ITENS_PERDIDOS
            or self.pontuacao <= PONTUACAO_LIMITE_INFERIOR
        ):
            self.estado = self.FIM

    def mover_jogadores(self, dt):
        meia = LARGURA_JOGADOR / 2
        camera_ativa = self.p1.alvo_x is not None or (
            self.p2 is not None and self.p2.alvo_x is not None
        )
        velocidade = VELOCIDADE_JOGADOR_CAMERA if camera_ativa else VELOCIDADE_JOGADOR
        p1_atual = self.p1.x
        novo_p1 = clamp(
            p1_atual + self.p1.deslocamento(dt, velocidade),
            meia,
            LARGURA - meia,
        )
        if self.p2 is None:
            self.p1.x = novo_p1
            return

        p2_atual = self.p2.x
        novo_p2 = clamp(
            p2_atual + self.p2.deslocamento(dt, velocidade),
            meia,
            LARGURA - meia,
        )

        if novo_p2 - novo_p1 < LARGURA_JOGADOR:
            deslocamento_p1 = novo_p1 - p1_atual
            deslocamento_p2 = novo_p2 - p2_atual
            empurrando_um_contra_o_outro = (
                deslocamento_p1 > 0 and deslocamento_p2 < 0
            )
            if empurrando_um_contra_o_outro:
                novo_p1, novo_p2 = p1_atual, p2_atual
            elif deslocamento_p1 > 0:
                novo_p1 = novo_p2 - LARGURA_JOGADOR
            else:
                novo_p2 = novo_p1 + LARGURA_JOGADOR

        self.p1.x = clamp(novo_p1, meia, LARGURA - meia)
        self.p2.x = clamp(novo_p2, meia, LARGURA - meia)

    def verificar_capturas(self):
        for item in self.itens:
            if self.estado == self.FIM:
                break
            if not item.ativo:
                continue
            for jogador in self.jogadores:
                if colide(item.retangulo(), jogador.retangulo()):
                    if item.tipo == jogador.tipo_alvo:
                        self.pontuacao += PONTOS_ACERTO
                    else:
                        self.pontuacao += PONTOS_ERRO
                    item.ativo = False
                    if self.pontuacao <= PONTUACAO_LIMITE_INFERIOR:
                        self.estado = self.FIM
                    break

        if PONTUACAO_MINIMA is not None:
            self.pontuacao = max(PONTUACAO_MINIMA, self.pontuacao)
        self.remover_itens_inativos()

    def remover_itens_inativos(self):
        self.itens = [item for item in self.itens if item.ativo]

    @property
    def jogadores(self):
        return (self.p1, self.p2) if self.p2 is not None else (self.p1,)

    def _contar_itens_perdidos(self):
        restantes = []
        for item in self.itens:
            if item.saiu_da_tela():
                self.itens_perdidos += 1
            else:
                restantes.append(item)
        self.itens = restantes
