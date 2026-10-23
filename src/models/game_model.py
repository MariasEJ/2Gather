import math
import random

from src.config import (
    LARGURA,
    LARGURA_JOGADOR,
    MAX_ITENS_PERDIDOS,
    NUM_PARTICOES,
    PONTOS_ACERTO,
    PONTOS_ERRO,
    PONTUACAO_LIMITE_INFERIOR,
    PONTUACAO_MINIMA,
    VELOCIDADE_JOGADOR,
    VELOCIDADE_JOGADOR_CAMERA,
    TEMPO_CONTAGEM,
)
from src.models.item_spawner import ItemSpawner
from src.models.fundos import FUNDOS
from src.models.lixeiras import LIXEIRAS, Lixeira
from src.models.particoes import centro_particao


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


class GameModel:
    MENU = "MENU"
    REGRAS = "REGRAS"
    CALIBRANDO = "CALIBRANDO"
    CONTAGEM = "CONTAGEM"
    JOGANDO = "JOGANDO"
    FIM = "FIM"

    def __init__(self, *, rng=None, rng_fundo=None):
        self.rng = rng if rng is not None else random.Random()
        self.rng_fundo = rng_fundo if rng_fundo is not None else random.Random()
        self.fundo = None
        self.reset()

    def reset(self):
        self.p1 = Lixeira('P1', centro_particao(NUM_PARTICOES // 2 - 1))
        self.p2 = Lixeira('P2', centro_particao(NUM_PARTICOES // 2))
        self.itens = []
        self.spawner = None
        self.fundo = None
        self.tempo_contagem = 0.0
        self.pontuacao = 0
        self.itens_perdidos = 0
        self.estado = self.MENU
        self._estado_antes_regras = self.MENU

    def iniciar(self):
        if self.estado not in (self.MENU, self.CALIBRANDO, self.FIM):
            return
        categorias = self.rng.sample(LIXEIRAS, 2)
        self.reset()
        self.p1 = categorias[0]('P1', centro_particao(NUM_PARTICOES // 2 - 1))
        self.p2 = categorias[1]('P2', centro_particao(NUM_PARTICOES // 2))
        self.fundo = self.rng_fundo.choice(FUNDOS)
        self.spawner = ItemSpawner(categorias, self.rng)
        self.tempo_contagem = TEMPO_CONTAGEM
        self.estado = self.CONTAGEM

    @property
    def numero_contagem(self):
        return max(1, math.ceil(self.tempo_contagem - 1e-9))

    def iniciar_calibracao(self):
        if self.estado == self.MENU:
            self.estado = self.CALIBRANDO

    def mostrar_regras(self):
        if self.estado in (self.MENU, self.FIM):
            self._estado_antes_regras = self.estado
            self.estado = self.REGRAS

    def voltar_menu(self):
        if self.estado == self.REGRAS:
            self.estado = self._estado_antes_regras

    def update(self, dt):
        dt = max(0.0, float(dt))
        if self.estado == self.CONTAGEM:
            self.tempo_contagem = max(0.0, self.tempo_contagem - dt)
            if self.tempo_contagem <= 1e-9:
                self.tempo_contagem = 0.0
                self.estado = self.JOGANDO
                self.itens.append(self.spawner.gerar())
                self.spawner.timer = 0.0
            return
        if self.estado != self.JOGANDO:
            return

        self.mover_jogadores(dt)
        self.itens.extend(
            self.spawner.update(dt, self.pontuacao)
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
        camera_ativa = self.p1.alvo_x is not None or self.p2.alvo_x is not None
        velocidade = VELOCIDADE_JOGADOR_CAMERA if camera_ativa else VELOCIDADE_JOGADOR
        p1_atual = self.p1.x
        novo_p1 = clamp(
            p1_atual + self.p1.deslocamento(dt, velocidade),
            meia,
            LARGURA - meia,
        )
        p2_atual = self.p2.x
        novo_p2 = clamp(
            p2_atual + self.p2.deslocamento(dt, velocidade),
            meia,
            LARGURA - meia,
        )

        # Apenas P1 entra na primeira faixa; apenas P2 entra na última.
        largura_faixa = LARGURA / NUM_PARTICOES
        novo_p1 = min(novo_p1, LARGURA - largura_faixa - 1e-6)
        novo_p2 = max(novo_p2, largura_faixa)

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
            # Mesma faixa E contato com o desenho; entre contatos, prioriza o dono.
            candidatos = sorted(self.jogadores, key=lambda j: j.ID != item.categoria_id)
            for jogador in candidatos:
                if item.particao == jogador.particao and item.toca_jogador(jogador):
                    if item.categoria_id == jogador.ID:
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
        return (self.p1, self.p2)

    def _contar_itens_perdidos(self):
        restantes = []
        for item in self.itens:
            if item.saiu_da_tela():
                self.itens_perdidos += 1
            else:
                restantes.append(item)
        self.itens = restantes
