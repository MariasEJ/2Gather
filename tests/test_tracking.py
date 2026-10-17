import unittest

from src.config import TEMPO_ESTABILIDADE, TOLERANCIA_FRAMES
from src.vision.mapeamento import SuavizadorEMA, cx_para_jogo
from src.vision.player_tracker import PlayerTracker
from src.vision.tipos import PessoaDetectada, StatusJogadores


def pessoa(x, cor=None):
    return PessoaDetectada(x, 0.5, 0.2, cor, corpo_completo=False)


class TrackingTests(unittest.TestCase):
    def test_solo_with_hips_and_without_feet_calibrates_while_moving(self):
        tracker = PlayerTracker(1)
        self.assertFalse(tracker.atualizar([pessoa(0.3)], 0).prontos)
        estado = tracker.atualizar([pessoa(0.4)], TEMPO_ESTABILIDADE)
        self.assertTrue(estado.prontos)
        self.assertEqual(estado.p1_cx, 0.4)

    def test_short_flicker_does_not_restart_calibration(self):
        tracker = PlayerTracker(1)
        tracker.atualizar([pessoa(0.3)], 0)
        self.assertFalse(tracker.atualizar([], 0.5).prontos)
        self.assertTrue(tracker.atualizar([pessoa(0.3)], TEMPO_ESTABILIDADE).prontos)

    def test_long_absence_requires_new_calibration(self):
        tracker = PlayerTracker(1)
        tracker.atualizar([pessoa(0.3)], 0)
        tracker.atualizar([pessoa(0.3)], TEMPO_ESTABILIDADE)
        for i in range(TOLERANCIA_FRAMES):
            self.assertTrue(tracker.atualizar([], 2 + i * 0.1).prontos)
        self.assertEqual(tracker.atualizar([], 4).status, StatusJogadores.FALTA_JOGADOR)
        self.assertFalse(tracker.atualizar([pessoa(0.3)], 5).prontos)
        self.assertTrue(tracker.atualizar([pessoa(0.3)], 5 + TEMPO_ESTABILIDADE).prontos)

    def test_pair_needs_separate_sides(self):
        tracker = PlayerTracker(2)
        for t in (0, 2):
            self.assertFalse(tracker.atualizar([pessoa(0.2), pessoa(0.4)], t).prontos)
        tracker.atualizar([pessoa(0.2), pessoa(0.8)], 3)
        self.assertTrue(tracker.atualizar([pessoa(0.8), pessoa(0.2)], 4).prontos)

    def test_crossing_pauses_and_requires_repositioning(self):
        tracker = PlayerTracker(2)
        esquerda, direita = pessoa(0.3, (0, 255, 255)), pessoa(0.7, (90, 255, 255))
        tracker.atualizar([esquerda, direita], 0)
        tracker.atualizar([esquerda, direita], 1)
        cruzadas = [pessoa(0.7, esquerda.cor), pessoa(0.3, direita.cor)]
        self.assertEqual(tracker.atualizar(cruzadas, 2).status, StatusJogadores.CRUZARAM)
        self.assertFalse(tracker.atualizar([esquerda, direita], 3).prontos)
        self.assertTrue(tracker.atualizar([esquerda, direita], 4).prontos)

    def test_mapping_and_smoothing(self):
        self.assertEqual(cx_para_jogo(0), 30)
        self.assertEqual(cx_para_jogo(0.5), 400)
        self.assertEqual(cx_para_jogo(1), 770)
        ema = SuavizadorEMA(0.5)
        self.assertEqual(ema.aplicar(100), 100)
        self.assertEqual(ema.aplicar(200), 150)
        ema.reset()
        self.assertEqual(ema.aplicar(200), 200)
