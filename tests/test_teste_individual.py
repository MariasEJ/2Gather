import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

import teste
from teste import LeitorMovimentos, PoseIndividual
from src.vision.tipos import PessoaDetectada, QuadroVisao


class TesteIndividualTests(unittest.TestCase):
    def setUp(self):
        self.leitor = LeitorMovimentos()
        self.pessoa = PessoaDetectada(0.5, 0.55, 0.2, foot_y=0.95)

    def calibrar(self):
        for i in range(31):
            self.assertEqual(self.leitor.atualizar(self.pessoa, i * 0.04), [])
        self.assertTrue(self.leitor.calibrado)

    def test_calibration_requires_one_visible_standing_person_with_feet(self):
        sem_pes = replace(self.pessoa, foot_y=None)
        for i in range(40):
            self.assertEqual(self.leitor.atualizar(sem_pes, i * 0.04), [])
        self.assertFalse(self.leitor.calibrado)

    def test_jump_and_squat_print_once_per_movement(self):
        self.calibrar()
        pulo = replace(self.pessoa, cy=0.47, foot_y=0.89)
        self.assertEqual(self.leitor.atualizar(pulo, 1.24), ['pulo'])
        self.assertEqual(self.leitor.atualizar(pulo, 1.28), [])
        self.leitor.atualizar(self.pessoa, 1.32)
        agachado = replace(self.pessoa, cy=0.65)
        self.assertEqual(self.leitor.atualizar(agachado, 1.36), ['agachar'])
        self.assertEqual(self.leitor.atualizar(agachado, 1.4), [])
        self.leitor.atualizar(self.pessoa, 1.44)
        self.assertEqual(self.leitor.atualizar(agachado, 1.48), ['agachar'])

    def test_lateral_movement_uses_direction_not_side_of_image(self):
        self.calibrar()
        self.assertEqual(self.leitor.atualizar(replace(self.pessoa, cx=0.6), 1.24), ['direita'])
        # Mesmo à direita do centro, voltar para 0.55 é deslocar à esquerda.
        self.assertEqual(self.leitor.atualizar(replace(self.pessoa, cx=0.55), 1.28), ['esquerda'])
        self.assertEqual(self.leitor.atualizar(replace(self.pessoa, cx=0.55), 1.32), [])

    def test_small_jitter_and_repeated_samples_do_not_print(self):
        self.calibrar()
        for i in range(1, 10):
            pessoa = replace(self.pessoa, cx=0.5 + 0.005 * (-1) ** i)
            self.assertEqual(self.leitor.atualizar(pessoa, 1.2 + i * 0.04), [])
        self.assertEqual(self.leitor.atualizar(replace(self.pessoa, cx=0.8), 1.56), [])

    def test_pose_loss_clears_motion_and_recalibration_clears_baselines(self):
        self.calibrar()
        self.assertEqual(self.leitor.atualizar(None, 1.24), [])
        reaparecendo = replace(self.pessoa, cx=0.7, cy=0.47, foot_y=0.89)
        self.assertEqual(self.leitor.atualizar(reaparecendo, 1.28), [])
        self.leitor.recalibrar()
        self.assertFalse(self.leitor.calibrado)
        self.assertEqual(self.leitor.atualizar(self.pessoa, 1.32), [])

    def test_detector_processes_full_frame_for_one_person(self):
        pontos = [SimpleNamespace(x=0.5, y=0.55, visibility=0.9) for _ in range(33)]
        pontos[27].y = pontos[28].y = 0.95
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with patch('teste.PoseDetector._criar_pose') as criar, \
                patch('teste.mp.solutions.drawing_utils.draw_landmarks'):
            criar.return_value.process.return_value = SimpleNamespace(
                pose_landmarks=SimpleNamespace(landmark=pontos))
            detector = PoseIndividual()
            try:
                pessoas, anotado = detector.detectar_e_desenhar(frame)
                self.assertEqual(len(pessoas), 1)
                self.assertEqual(pessoas[0].cx, 0.5)
                self.assertEqual(anotado.shape, frame.shape)
                self.assertEqual(criar.return_value.process.call_args.args[0].shape, frame.shape)
            finally:
                detector.fechar()
            criar.return_value.close.assert_called_once()

    def test_script_prints_movements_and_releases_camera_on_quit(self):
        pessoas = [self.pessoa] * 31 + [
            replace(self.pessoa, cy=0.47, foot_y=0.89),
            self.pessoa,
            replace(self.pessoa, cy=0.65),
            replace(self.pessoa, cx=0.6),
            replace(self.pessoa, cx=0.55),
        ]
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        quadros = [QuadroVisao([p], frame, 10000 + i * 40) for i, p in enumerate(pessoas)]
        with patch('teste.CameraWorker') as worker, \
                patch('teste.time.monotonic', return_value=10), \
                patch('builtins.print') as imprimir, \
                patch.multiple('teste.cv2', namedWindow=Mock(), imshow=Mock(),
                               putText=Mock(), destroyWindow=Mock(),
                               getWindowProperty=Mock(return_value=1),
                               waitKey=Mock(side_effect=[-1] * (len(quadros) - 1) + [ord('q')])):
            worker.return_value.erro = None
            worker.return_value.ultimo.side_effect = quadros
            self.assertEqual(teste.main(), 0)
            mensagens = [chamada.args[0] for chamada in imprimir.call_args_list]
            self.assertEqual(mensagens[-4:], ['pulo', 'agachar', 'direita', 'esquerda'])
            worker.return_value.parar.assert_called_once()
            teste.cv2.destroyWindow.assert_called_once_with(teste.JANELA)
