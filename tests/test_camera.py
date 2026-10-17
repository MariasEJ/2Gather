import time
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

    def test_two_regions_are_processed_and_drawn(self):
        detector = PoseDetector.__new__(PoseDetector)
        detector.num_jogadores = 2
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
        self.entrada = CameraInput(1)
        self.addCleanup(self.entrada.fechar)

    def quadro(self, timestamp, pessoas=None):
        if pessoas is None:
            pessoas = [PessoaDetectada(0.5, 0.5, 0.2)]
        return QuadroVisao(pessoas, None, timestamp)

    def test_fresh_pose_calibrates_and_starts_model(self):
        agora = time.monotonic()
        self.worker.ultimo.return_value = self.quadro(int((agora - 1.1) * 1000))
        self.assertFalse(self.entrada.ler().prontos)
        self.worker.ultimo.return_value = self.quadro(int(agora * 1000))
        entrada = self.entrada.ler()
        self.assertTrue(entrada.prontos)
        controller = GameController.__new__(GameController)
        controller.model = GameModel(1)
        controller.model.iniciar_calibracao()
        controller._aplicar_entrada(entrada)
        self.assertEqual(controller.model.estado, GameModel.JOGANDO)
        self.assertEqual(controller.model.p1.alvo_x, 400)

    def test_repeated_frame_cannot_advance_calibration(self):
        self.worker.ultimo.return_value = self.quadro(int(time.monotonic() * 1000))
        primeira = self.entrada.ler()
        for _ in range(20):
            self.assertIs(self.entrada.ler(), primeira)
        self.assertFalse(primeira.prontos)

    def test_frozen_frame_invalidates_ready_input(self):
        self.test_fresh_pose_calibrates_and_starts_model()
        self.worker.ultimo.return_value = self.quadro(int((time.monotonic() - CAMERA_TIMEOUT_QUADRO - 1) * 1000))
        self.assertFalse(self.entrada.ler().prontos)
        self.assertIn("quadros novos", self.entrada.erro)

    def test_initialization_timeout(self):
        self.entrada._inicio -= CAMERA_TIMEOUT_INICIAL + 1
        self.assertFalse(self.entrada.ler().prontos)
        self.assertIn("primeiro quadro", self.entrada.erro)

    def test_q_destroys_window_and_closes_worker_once(self):
        cv2.waitKey.return_value = ord("q")
        self.entrada.ler()
        self.entrada.fechar()
        self.assertIsNotNone(self.entrada.erro)
        self.worker.parar.assert_called_once()
        cv2.destroyWindow.assert_called_once()


class WorkerTests(unittest.TestCase):
    def test_capture_and_detector_are_released_after_inference_error(self):
        cv = Mock()
        cap = cv.VideoCapture.return_value
        cap.isOpened.return_value = True
        cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        detector = Mock()
        detector.detectar_e_desenhar.side_effect = RuntimeError("erro de inferencia simulado")
        worker = CameraWorker(1, cv, Mock(return_value=detector))
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
        worker = CameraWorker(1, cv)
        with self.assertLogs("src.vision.camera_worker", level="ERROR"):
            worker.start()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertIn("índice", worker.erro)
        cv.VideoCapture.return_value.release.assert_called_once()
