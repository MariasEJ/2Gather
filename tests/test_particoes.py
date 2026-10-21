import unittest

from src.config import ALTURA_JOGADOR, CHAO_Y, LARGURA, LARGURA_JOGADOR
from src.models.game_model import GameModel
from src.models.particoes import centro_particao, particao_x
from src.vision.mapeamento import cx_dupla_para_jogo


class ParticoesTests(unittest.TestCase):
    def test_edges_initial_positions_and_fixed_dimensions(self):
        for i in range(6):
            self.assertEqual(particao_x(i * LARGURA / 6), i)
            self.assertEqual(particao_x(centro_particao(i)), i)
        self.assertEqual(particao_x(LARGURA), 5)
        model = GameModel()
        self.assertEqual((model.p1.particao, model.p2.particao), (2, 3))
        for jogador in model.jogadores:
            self.assertEqual((jogador.y, jogador.largura, jogador.altura),
                             (CHAO_Y - ALTURA_JOGADOR, LARGURA_JOGADOR, ALTURA_JOGADOR))

    def test_extreme_lanes_and_contact_never_overlap_or_cross(self):
        for alvos in ((-100, -100), (900, 900), (400, 365), (245, 100), (500, 100)):
            model = GameModel()
            model.p1.alvo_x, model.p2.alvo_x = alvos
            for _ in range(60):
                model.mover_jogadores(0.1)
                self.assertLess(model.p1.particao, 5)
                self.assertGreater(model.p2.particao, 0)
                self.assertGreaterEqual(model.p2.x - model.p1.x, LARGURA_JOGADOR - 1e-6)
                self.assertGreaterEqual(model.p1.x, 48)
                self.assertLessEqual(model.p2.x, 752)
                for jogador in model.jogadores:
                    self.assertEqual((jogador.y, jogador.largura, jogador.altura),
                                     (CHAO_Y - ALTURA_JOGADOR, LARGURA_JOGADOR, ALTURA_JOGADOR))

    def test_opposing_players_stop(self):
        model = GameModel()
        model.p1.x, model.p2.x = 300, 396
        model.p1.alvo_x, model.p2.alvo_x = 500, 100
        model.mover_jogadores(0.1)
        self.assertEqual((model.p1.x, model.p2.x), (300, 396))

    def test_camera_half_can_reach_all_five_allowed_lanes(self):
        for jogador, minimo, maximo, faixas in ((1, 0.1, 0.45, range(5)), (2, 0.55, 0.9, range(1, 6))):
            atingidas = {particao_x(cx_dupla_para_jogo(minimo + (maximo - minimo) * i / 100, jogador))
                        for i in range(101)}
            self.assertEqual(atingidas, set(faixas))
