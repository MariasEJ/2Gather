import unittest
from types import SimpleNamespace

from src.vision.gestos import detectar_gestos, esta_agachado


def pose(agachado=False, bracos_x=False):
    pontos = [SimpleNamespace(x=0.5, y=0.5, visibility=0.9) for _ in range(33)]
    coordenadas = {
        11: (0.35, 0.2), 12: (0.65, 0.2),
        13: (0.3, 0.45), 14: (0.7, 0.45),
        15: (0.3, 0.6), 16: (0.7, 0.6),
        23: (0.4, 0.55), 24: (0.6, 0.55),
        25: (0.4, 0.75), 26: (0.6, 0.75),
        27: (0.4, 0.95), 28: (0.6, 0.95),
    }
    if agachado:
        coordenadas.update({23: (0.4, 0.65), 24: (0.6, 0.65), 25: (0.25, 0.75), 26: (0.75, 0.75)})
    if bracos_x:
        coordenadas.update({15: (0.65, 0.25), 16: (0.35, 0.25)})
    for i, (x, y) in coordenadas.items():
        pontos[i].x, pontos[i].y = x, y
    return pontos


class GestosTests(unittest.TestCase):
    def test_standing_and_lowered_arms_are_not_gestures(self):
        self.assertEqual(detectar_gestos(pose(), 320, 480), (False, False))

    def test_hip_threshold_is_strict_and_individual(self):
        self.assertFalse(esta_agachado(0.54, 0.50))
        self.assertFalse(esta_agachado(0.55, 0.50))
        self.assertTrue(esta_agachado(0.56, 0.50))
        self.assertFalse(esta_agachado(0.56, 0.60))
        self.assertFalse(esta_agachado(0.8, None))
        self.assertFalse(esta_agachado(0.8, 0.5, 0.1))

    def test_squat_uses_hips_without_knees_or_ankles(self):
        pontos = pose(agachado=True)
        for i in (25, 26, 27, 28):
            pontos[i].visibility = 0
        self.assertEqual(detectar_gestos(pontos, 320, 480, 0.55), (True, False))

    def test_crossed_forearms_detect_x(self):
        self.assertEqual(detectar_gestos(pose(bracos_x=True), 320, 480), (False, True))

    def test_missing_or_invalid_landmarks_do_not_trigger(self):
        for i, gesto in ((23, 0), (15, 1)):
            for atributo, valor in (("visibility", 0.1), ("x", float("nan")), ("y", 2)):
                with self.subTest(i=i, atributo=atributo):
                    pontos = pose(agachado=True, bracos_x=True)
                    setattr(pontos[i], atributo, valor)
                    self.assertFalse(detectar_gestos(pontos, 320, 480, 0.55)[gesto])
