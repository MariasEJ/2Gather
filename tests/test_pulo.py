import unittest

from src.vision.gestos import DetectorPulo


class PuloTests(unittest.TestCase):
    def setUp(self):
        self.detector = DetectorPulo()

    def ler(self, hip, foot, agora, **kwargs):
        return self.detector.atualizar(hip, foot, 0.55, 0.95, agora, **kwargs)

    def test_rising_hips_and_feet_trigger_once_until_landing(self):
        self.assertFalse(self.ler(0.55, 0.95, 0))
        self.assertTrue(self.ler(0.47, 0.89, 0.1))
        self.assertFalse(self.ler(0.44, 0.87, 0.14))
        self.assertFalse(self.ler(0.47, 0.89, 0.2))
        self.assertFalse(self.ler(0.55, 0.95, 0.3))
        self.assertFalse(self.ler(0.47, 0.89, 0.4))  # Ainda no cooldown.
        self.ler(0.55, 0.95, 0.7)
        self.assertTrue(self.ler(0.47, 0.89, 0.8))

    def test_squat_tip_toes_and_noise_are_not_jumps(self):
        for hip, foot in ((0.65, 0.95), (0.47, 0.95), (0.55, 0.89), (0.54, 0.94)):
            with self.subTest(hip=hip, foot=foot):
                self.detector = DetectorPulo()
                self.ler(0.55, 0.95, 0)
                self.assertFalse(self.ler(hip, foot, 0.1))

    def test_slow_rise_and_descent_do_not_trigger(self):
        self.ler(0.55, 0.95, 0)
        for i in range(1, 11):
            self.assertFalse(self.ler(0.55 - i * 0.01, 0.95 - i * 0.01, i * 0.1))
        self.assertFalse(self.ler(0.47, 0.89, 1.1))

    def test_jump_speed_is_independent_of_capture_frame_rate(self):
        for intervalo in (1 / 15, 1 / 30, 1 / 60):
            with self.subTest(intervalo=intervalo):
                self.detector = DetectorPulo()
                self.ler(0.55, 0.95, 0)
                eventos = []
                for i in range(1, int(0.2 / intervalo) + 1):
                    subida = 0.6 * i * intervalo
                    eventos.append(self.ler(0.55 - subida, 0.95 - subida, i * intervalo))
                self.assertEqual(eventos.count(True), 1)

    def test_missing_feet_or_low_confidence_cannot_trigger(self):
        for hip, foot, confianca in ((0.47, None, 1), (0.47, 0.89, 0.1),
                                     (float('nan'), 0.89, 1), (0.47, -0.1, 1)):
            with self.subTest(hip=hip, foot=foot, confianca=confianca):
                self.detector = DetectorPulo()
                self.ler(0.55, 0.95, 0)
                self.assertFalse(self.ler(hip, foot, 0.1, confianca=confianca))
                self.assertFalse(self.ler(0.47, 0.89, 0.14))

    def test_no_jump_before_calibration_or_on_first_returning_sample(self):
        self.assertFalse(self.detector.atualizar(0.47, 0.89, None, None, 0))
        self.assertFalse(self.ler(0.47, 0.89, 0.1))
        self.ler(0.55, 0.95, 0.2)
        self.assertFalse(self.ler(0.47, 0.89, 1.2))

    def test_duplicate_timestamp_does_not_create_second_event(self):
        self.ler(0.55, 0.95, 0)
        self.assertTrue(self.ler(0.47, 0.89, 0.1))
        self.assertFalse(self.ler(0.47, 0.89, 0.1))
