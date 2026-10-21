import time
from dataclasses import replace
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np

from src.config import CAMERA_TIMEOUT_INICIAL, CAMERA_TIMEOUT_QUADRO
from src.controllers.input.camera_input import CameraInput
from src.controllers.game_controller import GameController
from src.models.game_model import GameModel
from src.vision.camera_worker import CameraWorker
from src.vision.pose_detector import PoseDetector
from src.vision.tipos import PessoaDetectada, QuadroVisao


def landmarks(visibilidade=0.9):
    pontos = [SimpleNamespace(x=0.5, y=0.5, visibility=visibilidade) for _ in range(33)]
    pontos[11].x, pontos[12].x = 0.4, 0.6
    pontos[23].x, pontos[24].x = 0.45, 0.55
    return pontos


class PoseTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_visible_hips_are_enough_even_without_feet(self):
        pontos = landmarks()
        pontos[27].visibility = pontos[28].visibility = 0
        pessoa = PoseDetector._extrair_pessoa(pontos, self.frame, 0, 640, 640)
        self.assertIsNotNone(pessoa)
        self.assertFalse(pessoa.corpo_completo)
        self.assertEqual(pessoa.cx, 0.5)

    def test_moderate_visibility_is_not_confused_with_detection_confidence(self):
        pessoa = PoseDetector._extrair_pessoa(landmarks(0.4), self.frame, 0, 640, 640)
        self.assertIsNotNone(pessoa)

    def test_invalid_or_invisible_hip_cannot_control(self):
        for campo, valor in (("visibility", 0.1), ("x", float("nan")), ("y", 1.2)):
            with self.subTest(campo=campo):
                pontos = landmarks()
                setattr(pontos[23], campo, valor)
                self.assertIsNone(PoseDetector._extrair_pessoa(pontos, self.frame, 0, 640, 640))

    def test_half_frame_coordinates_are_mapped_to_full_frame(self):
        esquerda = PoseDetector._extrair_pessoa(landmarks(), self.frame, 0, 320, 640)
        direita = PoseDetector._extrair_pessoa(landmarks(), self.frame, 320, 320, 640)
        self.assertEqual((esquerda.cx, direita.cx), (0.25, 0.75))
        self.assertEqual((esquerda.hip_y, direita.hip_y), (0.5, 0.5))
        self.assertEqual(esquerda.confianca_quadris, 0.9)

    def test_two_regions_are_processed_and_drawn(self):
        detector = PoseDetector.__new__(PoseDetector)
        detector._ultimo_log = float("-inf")
        detector.mp_pose = Mock()
        detector.mp_drawing = Mock()
        detector._poses = [Mock(), Mock()]
        for pose in detector._poses:
            pose.process.return_value = SimpleNamespace(pose_landmarks=SimpleNamespace(landmark=landmarks()))
        pessoas, anotado = detector.detectar_e_desenhar(self.frame)
        self.assertEqual([p.cx for p in pessoas], [0.25, 0.75])
        self.assertEqual(detector.mp_drawing.draw_landmarks.call_count, 2)
        self.assertEqual(anotado.shape, self.frame.shape)
        self.assertFalse(np.array_equal(anotado, self.frame))


class CameraInputTests(unittest.TestCase):
    def setUp(self):
        for nome in ("namedWindow", "destroyWindow", "imshow", "putText"):
            patcher = patch.object(cv2, nome)
            patcher.start()
            self.addCleanup(patcher.stop)
        for nome, valor in (("waitKey", -1), ("getWindowProperty", 1)):
            patcher = patch.object(cv2, nome, return_value=valor)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch("src.controllers.input.camera_input.CameraWorker")
        self.worker = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.worker.erro = None
        self.worker.ultimo.return_value = None
        self.entrada = CameraInput()
        self.addCleanup(self.entrada.fechar)

    def pessoas(self, agachados=(False, False)):
        return [PessoaDetectada(x, 0.5 + (0.1 if agachado else 0), 0.2, cor)
                for x, cor, agachado in zip((0.25, 0.75), ((0, 255, 255), (90, 255, 255)), agachados)]

    def ler_quadro(self, segundo, pessoas=None):
        pessoas = self.pessoas() if pessoas is None else pessoas
        self.worker.ultimo.return_value = QuadroVisao(pessoas, None, round(segundo * 1000))
        with patch('src.controllers.input.camera_input.time.monotonic', return_value=segundo):
            return self.entrada.ler()

    def calibrar(self):
        self.inicio = time.monotonic()
        for i in range(31):
            entrada = self.ler_quadro(self.inicio + i * 0.04)
        self.assertTrue(entrada.prontos)
        self.assertFalse(entrada.agachamento_confirmado)
        return self.inicio + 1.2

    def test_fresh_hips_calibrate_and_confirm_pair(self):
        agora = self.calibrar()
        self.assertFalse(self.ler_quadro(agora + 0.1, self.pessoas((True, True))).agachamento_confirmado)
        entrada = self.ler_quadro(agora + 0.7, self.pessoas((True, True)))
        self.assertTrue(entrada.agachamento_confirmado)
        self.assertTrue(entrada.agachado_p1 and entrada.agachado_p2)
        self.assertIsNotNone(entrada.alvo_p1)
        self.assertIsNotNone(entrada.alvo_p2)

    def test_missing_pose_discards_old_target_and_gesture(self):
        agora = self.calibrar()
        self.ler_quadro(agora + 0.1, self.pessoas((True, True)))
        entrada = self.ler_quadro(agora + 0.8, [self.pessoas()[0]])
        self.assertFalse(entrada.prontos or entrada.agachamento_confirmado)
        self.assertIsNotNone(entrada.alvo_p1)
        self.assertIsNone(entrada.alvo_p2)

    def test_pair_squat_confirmation_requires_overlap(self):
        agora = self.calibrar()
        for segundo, agachados, esperado in (
            (0.1, (True, False), False), (1, (False, True), False),
            (2, (True, True), False), (2.7, (True, True), True),
            (2.8, (False, True), False),
        ):
            entrada = self.ler_quadro(agora + segundo, self.pessoas(agachados))
            self.assertEqual(entrada.agachamento_confirmado, esperado)

    def test_repeated_frame_cannot_advance_calibration_or_confirm(self):
        agora = time.monotonic()
        self.ler_quadro(agora)
        for _ in range(40):
            entrada = self.entrada.ler()
            self.assertFalse(entrada.prontos or entrada.amostra_nova or entrada.agachamento_confirmado)
        self.entrada.recalibrar()
        agora = self.calibrar()
        self.ler_quadro(agora + 0.1, self.pessoas((True, True)))
        self.ler_quadro(agora + 0.8, self.pessoas((True, True)))
        self.assertFalse(self.entrada.ler().agachamento_confirmado)
        self.assertFalse(self.entrada.ler().amostra_nova)

    def test_frozen_frame_invalidates_ready_input(self):
        agora = self.calibrar()
        with patch('src.controllers.input.camera_input.time.monotonic', return_value=agora + CAMERA_TIMEOUT_QUADRO + 1):
            entrada = self.entrada.ler()
        self.assertFalse(entrada.prontos)
        self.assertIsNone(entrada.alvo_p1)
        self.assertIn('quadros novos', self.entrada.erro)

    def test_initialization_timeout(self):
        self.entrada._inicio -= CAMERA_TIMEOUT_INICIAL + 1
        self.assertFalse(self.entrada.ler().prontos)
        self.assertIn('primeiro quadro', self.entrada.erro)

    def test_failure_keeps_camera_source_and_neutral_input(self):
        self.calibrar()
        self.worker.erro = 'Captura indisponível'
        entrada = self.entrada.ler()
        self.assertFalse(entrada.prontos)
        self.assertIsNone(entrada.alvo_p1)
        self.assertIsNone(entrada.alvo_p2)
        self.assertIn('Câmera indisponível', entrada.aviso)
        self.assertIsInstance(self.entrada, CameraInput)

    def test_q_or_close_destroys_window_and_closes_worker_once(self):
        cv2.waitKey.return_value = ord('q')
        self.entrada.ler()
        self.entrada.fechar()
        self.assertIsNotNone(self.entrada.erro)
        self.worker.parar.assert_called_once()
        cv2.destroyWindow.assert_called_once()
        self.assertFalse(self.entrada.ler().prontos)

    def test_closed_window_never_enables_keyboard(self):
        cv2.getWindowProperty.return_value = 0
        entrada = self.entrada.ler()
        self.assertFalse(entrada.prontos)
        self.assertFalse(entrada.valido_p1 or entrada.valido_p2)
        self.assertIsInstance(self.entrada, CameraInput)

    def test_camera_window_initialization_error_stays_unavailable(self):
        with patch.object(cv2, 'namedWindow', side_effect=cv2.error('sem janela')):
            with self.assertLogs('src.controllers.input.camera_input', level='ERROR'):
                fonte = CameraInput()
        self.addCleanup(fonte.fechar)
        self.assertFalse(fonte.ler().prontos)
        self.assertIsNone(fonte.worker)


class WorkerTests(unittest.TestCase):
    def test_capture_and_detector_are_released_after_inference_error(self):
        cv = Mock()
        cap = cv.VideoCapture.return_value
        cap.isOpened.return_value = True
        cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        detector = Mock()
        detector.detectar_e_desenhar.side_effect = RuntimeError("erro de inferencia simulado")
        worker = CameraWorker(cv, Mock(return_value=detector))
        cv.VideoCapture.assert_not_called()
        with self.assertLogs("src.vision.camera_worker", level="ERROR"):
            worker.start()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertIn("simulado", worker.erro)
        cap.release.assert_called_once()
        detector.fechar.assert_called_once()

    def test_camera_open_failure_is_reported(self):
        cv = Mock()
        cv.VideoCapture.return_value.isOpened.return_value = False
        worker = CameraWorker(cv)
        with self.assertLogs("src.vision.camera_worker", level="ERROR"):
            worker.start()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertIn("índice", worker.erro)
        cv.VideoCapture.return_value.release.assert_called_once()
