import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.controllers.game_controller import GameController
from src.controllers.input.input_source import EntradaJogadores
from src.controllers.input.keyboard_input import KeyboardInput
from src.controllers.input_controller import InputController
from src.models.falling_item import FallingItem
from src.models.game_model import GameModel
from src.vision.tipos import StatusJogadores


class GameFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def controller(self, jogadores=1):
        return GameController(num_jogadores=jogadores)

    def test_space_keyboard_starts_and_moves(self):
        controller = self.controller()
        InputController().tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE), controller.model)
        self.assertEqual(controller.model.estado, GameModel.CALIBRANDO)
        controller._aplicar_entrada(EntradaJogadores(dir_p1=1))
        anterior = controller.model.p1.x
        controller.model.update(0.1)
        self.assertEqual(controller.model.estado, GameModel.JOGANDO)
        self.assertGreater(controller.model.p1.x, anterior)

    def test_camera_start_pause_resume_and_manual_pause(self):
        controller = self.controller(2)
        model = controller.model
        model.iniciar_calibracao()
        controller._aplicar_entrada(EntradaJogadores(prontos=False, status=StatusJogadores.REPOSICIONANDO))
        self.assertEqual(model.estado, model.CALIBRANDO)
        controller._aplicar_entrada(EntradaJogadores(alvo_p1=100, alvo_p2=700))
        self.assertEqual(model.estado, model.JOGANDO)
        self.assertEqual(model.p1.alvo_x, 100)
        item = FallingItem(400, "circulo", (0, 0, 0), 150)
        model.itens.append(item)
        controller._aplicar_entrada(EntradaJogadores(status=StatusJogadores.FALTA_JOGADOR, prontos=False))
        model.update(1)
        self.assertEqual(model.estado, model.PAUSADO_POSICAO)
        self.assertEqual(item.y, -item.tamanho)
        controller._aplicar_entrada(EntradaJogadores(alvo_p1=150, alvo_p2=650))
        self.assertEqual(model.estado, model.JOGANDO)
        self.assertEqual(model.p1.alvo_x, 150)
        model.pausar()
        controller._aplicar_entrada(EntradaJogadores(alvo_p1=200, alvo_p2=600))
        self.assertEqual(model.estado, model.PAUSADO)

    def test_failure_falls_back_to_keyboard_from_calibration(self):
        controller = self.controller()
        camera = Mock(erro="camera desconectada")
        controller.input_source = camera
        controller.model.iniciar_calibracao()
        with self.assertLogs("src.controllers.game_controller", level="WARNING"):
            self.assertTrue(controller._trocar_para_teclado_se_camera_falhar())
        camera.fechar.assert_called_once()
        self.assertIsInstance(controller.input_source, KeyboardInput)
        controller._aplicar_entrada(controller.input_source.ler())
        self.assertEqual(controller.model.estado, GameModel.JOGANDO)

    def test_real_loop_start_recalibrates_and_closes(self):
        controller = self.controller()
        source = Mock(erro=None)
        source.ler.return_value = EntradaJogadores(dir_p1=1)
        controller.input_source = source
        controller.view.render = Mock(side_effect=lambda *args: setattr(controller, "rodando", False))
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        controller.run()
        self.assertEqual(controller.model.estado, GameModel.JOGANDO)
        source.recalibrar.assert_called_once()
        source.fechar.assert_called_once()

    def test_restart_goes_through_calibration(self):
        controller = self.controller()
        controller.model.estado = GameModel.FIM
        controller.model.pontuacao = 30
        InputController().tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r), controller.model)
        self.assertEqual(controller.model.estado, GameModel.CALIBRANDO)
        self.assertEqual(controller.model.pontuacao, 0)
        controller._aplicar_entrada(EntradaJogadores())
        self.assertEqual(controller.model.estado, GameModel.JOGANDO)


class ModelRulesTests(unittest.TestCase):
    def test_camera_targets_never_overlap_in_either_direction(self):
        for alvos in ((400, 365), (245, 100), (500, 100), (-500, -500), (2000, 2000)):
            with self.subTest(alvos=alvos):
                model = GameModel(2)
                model.p1.x, model.p2.x = 300, 365
                model.p1.alvo_x, model.p2.alvo_x = alvos
                for _ in range(50):
                    model.mover_jogadores(0.02)
                    self.assertGreaterEqual(model.p2.x - model.p1.x, 60)
                    self.assertGreaterEqual(model.p1.x, 30)
                    self.assertLessEqual(model.p2.x, 770)

    def test_opposing_players_stop(self):
        model = GameModel(2)
        model.p1.x, model.p2.x = 300, 360
        model.p1.alvo_x, model.p2.alvo_x = 500, 100
        model.mover_jogadores(0.1)
        self.assertEqual((model.p1.x, model.p2.x), (300, 360))

    def test_scoring_and_three_misses_end_game(self):
        model = GameModel(2)
        model.iniciar()
        for tipo, pontuacao in (("circulo", 1), ("quadrado", 0)):
            item = FallingItem(model.p1.x, tipo, (0, 0, 0), 0)
            item.y = model.p1.y
            model.itens = [item]
            model.update(0)
            self.assertEqual(model.pontuacao, pontuacao)
        model.itens = [FallingItem(400, "circulo", (0, 0, 0), 0) for _ in range(3)]
        for item in model.itens:
            item.y = 700
        model.update(0)
        self.assertEqual(model.estado, model.FIM)
        self.assertEqual(model.pontuacao, 0)
