import unittest
from dataclasses import replace

from src.vision.mapeamento import SuavizadorEMA, cx_dupla_para_jogo
from src.vision.player_tracker import PlayerTracker
from src.vision.tipos import PessoaDetectada, StatusJogadores


def dupla():
    return [PessoaDetectada(0.25, 0.5, 0.2, (0, 255, 255), corpo_completo=False),
            PessoaDetectada(0.75, 0.6, 0.2, (90, 255, 255), corpo_completo=False)]


def calibrar(tracker, pessoas=None, inicio=0):
    pessoas = dupla() if pessoas is None else pessoas
    for i in range(31):
        estado = tracker.atualizar(pessoas, inicio + i * 0.04)
    return estado


class TrackingTests(unittest.TestCase):
    def test_hips_alone_calibrate_separate_references(self):
        tracker = PlayerTracker()
        self.assertTrue(calibrar(tracker).prontos)
        self.assertEqual(tracker.referencias, [0.5, 0.6])
        pessoas = dupla()
        pessoas[0] = replace(pessoas[0], cy=0.56)
        estado = tracker.atualizar(pessoas, 2)
        self.assertTrue(estado.agachado_p1)
        self.assertFalse(estado.agachado_p2)

    def test_calibration_needs_new_samples_and_stable_hips(self):
        tracker = PlayerTracker()
        for _ in range(50):
            self.assertFalse(tracker.atualizar(dupla(), 0).prontos)
        pessoas = dupla()
        for i in range(31):
            pessoas[0] = replace(pessoas[0], cy=0.5 + i * 0.003)
            self.assertFalse(tracker.atualizar(pessoas, 1 + i * 0.04).prontos)

    def test_missing_pose_clears_old_targets_immediately(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        estado = tracker.atualizar([], 2)
        self.assertFalse(estado.prontos)
        self.assertIsNone(estado.p1_cx)
        self.assertIsNone(estado.p2_cx)
        self.assertFalse(estado.agachado_p1 or estado.agachado_p2)

    def test_brief_pose_loss_recovers_without_repeating_calibration(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        self.assertFalse(tracker.atualizar([], 1.24).prontos)
        estado = tracker.atualizar(dupla(), 1.28)
        self.assertTrue(estado.prontos)
        self.assertEqual((estado.p1_cx, estado.p2_cx), (0.25, 0.75))
        self.assertEqual(tracker.referencias, [0.5, 0.6])

    def test_long_pose_loss_still_requires_standing_confirmation(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        tracker.atualizar([], 1.24)
        self.assertFalse(tracker.atualizar(dupla(), 3).prontos)
        self.assertTrue(calibrar(tracker, inicio=3.04).prontos)

    def test_feet_can_calibrate_after_hips_without_restarting_player_control(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        pessoas = [replace(p, foot_y=0.95) for p in dupla()]
        for i in range(30):
            self.assertTrue(tracker.atualizar(pessoas, 1.24 + i * 0.04).prontos)
        self.assertEqual(tracker.referencias_pes, [0.95, 0.95])
        pessoas[1] = replace(pessoas[1], cy=0.52, foot_y=0.89)
        estado = tracker.atualizar(pessoas, 2.44)
        self.assertTrue(estado.pulou_p2)
        self.assertFalse(estado.pulou_p1)

    def test_missing_pose_does_not_turn_reappearance_in_air_into_jump(self):
        tracker = PlayerTracker()
        pessoas = [replace(p, foot_y=0.95) for p in dupla()]
        calibrar(tracker, pessoas)
        tracker.atualizar([], 1.24)
        pessoas[0] = replace(pessoas[0], cy=0.42, foot_y=0.89)
        estado = tracker.atualizar(pessoas, 1.28)
        self.assertFalse(estado.pulou_p1 or estado.pulou_p2)

    def test_fast_samples_do_not_fix_feet_before_hip_calibration(self):
        tracker = PlayerTracker()
        pessoas = [replace(p, foot_y=0.95) for p in dupla()]
        for i in range(40):
            tracker.atualizar(pessoas, i * 0.01)
        self.assertEqual(tracker.referencias_pes, [None, None])
        self.assertTrue(calibrar(tracker, pessoas, inicio=0.4).prontos)
        self.assertEqual(tracker.referencias_pes, [0.95, 0.95])

    def test_reliable_remaining_player_can_move(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        p1 = replace(dupla()[0], cx=0.3)
        estado = tracker.atualizar([p1], 2)
        self.assertEqual(estado.p1_cx, 0.3)
        self.assertIsNone(estado.p2_cx)
        self.assertFalse(estado.prontos)

    def test_ambiguous_identity_neutralizes_both(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        desconhecido = PessoaDetectada(0.5, 0.55, 0.2)
        estado = tracker.atualizar([desconhecido], 2)
        self.assertIsNone(estado.p1_cx)
        self.assertIsNone(estado.p2_cx)

    def test_recovery_never_recalibrates_while_crouched(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        tracker.atualizar([], 2)
        agachados = [replace(p, cy=p.cy + 0.1) for p in dupla()]
        self.assertFalse(calibrar(tracker, agachados, 3).prontos)
        self.assertEqual(tracker.referencias, [0.5, 0.6])
        self.assertTrue(calibrar(tracker, inicio=5).prontos)

    def test_crossing_keeps_identities_until_players_return(self):
        tracker = PlayerTracker()
        calibrar(tracker)
        cruzados = [replace(dupla()[0], cx=0.75), replace(dupla()[1], cx=0.25)]
        for i in range(40):
            estado = tracker.atualizar(cruzados, 2 + i * 0.04)
            self.assertEqual(estado.status, StatusJogadores.CRUZARAM)
            self.assertIsNone(estado.p1_cx)
            self.assertIsNone(estado.p2_cx)
        self.assertTrue(calibrar(tracker, inicio=5).prontos)
        self.assertEqual(tracker.referencias, [0.5, 0.6])

    def test_pair_needs_separate_sides(self):
        tracker = PlayerTracker()
        pessoas = dupla()
        pessoas[1] = replace(pessoas[1], cx=0.4)
        self.assertFalse(calibrar(tracker, pessoas).prontos)
        self.assertTrue(calibrar(tracker, inicio=3).prontos)

    def test_low_confidence_cannot_calibrate_or_trigger_squat(self):
        tracker = PlayerTracker()
        pessoas = [replace(p, confianca_quadris=0.1) for p in dupla()]
        self.assertFalse(calibrar(tracker, pessoas).prontos)
        calibrar(tracker, inicio=3)
        estado = tracker.atualizar(pessoas, 5)
        self.assertFalse(estado.prontos or estado.agachado_p1 or estado.agachado_p2)

    def test_mapping_and_smoothing(self):
        self.assertLess(cx_dupla_para_jogo(0, 1), cx_dupla_para_jogo(1, 1))
        ema = SuavizadorEMA(0.5)
        self.assertEqual(ema.aplicar(100), 100)
        self.assertEqual(ema.aplicar(200), 150)
        ema.reset()
        self.assertEqual(ema.aplicar(200), 200)
