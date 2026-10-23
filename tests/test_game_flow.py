import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from src.controllers.game_controller import GameController
from src.controllers.input.input_source import EntradaJogadores
from src.controllers.input.keyboard_input import KeyboardInput
from src.controllers.input_controller import InputController
from src.models.falling_item import FallingItem
from src.models.game_model import GameModel
from src.vision.tipos import StatusJogadores
from src.config import CHAO_Y, ALTURA_JOGADOR


class GameFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        # Gestos são simulados sem abrir a câmera; testes de teclado sobrescrevem o modo.
        modo = patch('src.config.USAR_CAMERA', True)
        modo.start()
        self.addCleanup(modo.stop)
        self.controller = GameController(input_source=KeyboardInput())
        self.model = self.controller.model
        self.controller._aplicar_entrada(EntradaJogadores())

    def agachar(self, **kwargs):
        return EntradaJogadores(agachado_p1=True, agachado_p2=True,
                                agachamento_confirmado=True, **kwargs)

    def test_pair_confirmation_enters_countdown_once(self):
        for entrada in (EntradaJogadores(agachado_p1=True), EntradaJogadores(agachado_p2=True),
                        EntradaJogadores(agachado_p1=True, agachado_p2=True)):
            self.controller._aplicar_entrada(entrada)
            self.assertEqual(self.model.estado, self.model.MENU)
        self.controller._aplicar_entrada(self.agachar())
        self.assertEqual(self.model.estado, self.model.CONTAGEM)
        categorias = tuple(type(j) for j in self.model.jogadores)
        self.model.update(1)
        self.controller._aplicar_entrada(self.agachar())
        self.assertEqual(self.model.tempo_contagem, 2)
        self.assertEqual(tuple(type(j) for j in self.model.jogadores), categorias)

    def test_no_controls_or_instructions_during_countdown(self):
        self.controller._aplicar_entrada(self.agachar())
        for tecla in (pygame.K_x, pygame.K_p, pygame.K_ESCAPE, pygame.K_w, pygame.K_UP):
            InputController().tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla), self.model)
        self.controller._aplicar_entrada(EntradaJogadores(dir_p1=-1, dir_p2=1, bracos_x=True, x_confirmado=True))
        self.model.mostrar_regras()
        self.model.update(1)
        self.assertEqual(self.model.estado, self.model.CONTAGEM)
        self.assertEqual((self.model.p1.particao, self.model.p2.particao), (1, 2))
        self.assertFalse(self.model.itens)

    def test_invalid_tracking_does_not_stop_countdown_or_game(self):
        self.controller._aplicar_entrada(self.agachar())
        invalida = EntradaJogadores(status=StatusJogadores.CRUZARAM, prontos=False)
        self.controller._aplicar_entrada(invalida)
        self.model.update(3)
        self.assertEqual(self.model.estado, self.model.JOGANDO)
        self.assertEqual(len(self.model.itens), 1)
        self.controller._aplicar_entrada(EntradaJogadores(alvo_p1=100, alvo_p2=700))
        self.controller._aplicar_entrada(invalida)
        self.assertIsNone(self.model.p1.alvo_x)
        self.assertIsNone(self.model.p2.alvo_x)
        self.assertEqual((self.model.p1.direcao, self.model.p2.direcao), (0, 0))
        self.model.itens = [FallingItem(20, type(self.model.p1).ITENS[0], type(self.model.p1).ID, 1000) for _ in range(3)]
        self.model.update(1)
        self.assertEqual(self.model.estado, self.model.FIM)
        self.assertEqual(self.model.itens_perdidos, 3)

    def test_one_reliable_player_continues_moving(self):
        self.model.iniciar()
        self.model.update(3)
        self.controller._aplicar_entrada(EntradaJogadores(
            status=StatusJogadores.FALTA_JOGADOR, prontos=False,
            alvo_p1=100, valido_p1=True, valido_p2=False))
        anterior = self.model.p2.x
        self.model.update(0.1)
        self.assertLess(self.model.p1.x, 333)
        self.assertEqual(self.model.p2.x, anterior)
        self.assertEqual(self.model.estado, self.model.JOGANDO)

    def test_squat_x_pause_and_escape_do_nothing_while_playing(self):
        self.model.iniciar()
        self.model.update(3)
        self.controller._aplicar_entrada(self.agachar(bracos_x=True, x_confirmado=True))
        for tecla in (pygame.K_x, pygame.K_p, pygame.K_ESCAPE):
            InputController().tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla), self.model)
        self.model.mostrar_regras()
        self.model.update(0.1)
        self.assertEqual(self.model.estado, self.model.JOGANDO)
        self.assertEqual((self.model.p1.y, self.model.p1.altura), (CHAO_Y - ALTURA_JOGADOR, ALTURA_JOGADOR))
        self.assertGreater(self.model.itens[0].y, -self.model.itens[0].altura)

    def test_restart_requires_release_in_results_and_new_confirmed_gesture(self):
        self.model.iniciar()
        self.model.update(3)
        self.model.estado = self.model.FIM
        self.model.pontuacao = 30
        self.controller._aplicar_entrada(self.agachar())
        self.assertEqual(self.model.estado, self.model.FIM)
        self.controller._aplicar_entrada(EntradaJogadores(prontos=False))
        self.controller._aplicar_entrada(self.agachar())
        self.assertEqual(self.model.estado, self.model.FIM)
        self.controller._aplicar_entrada(EntradaJogadores())
        self.controller._aplicar_entrada(self.agachar(amostra_nova=False))
        self.assertEqual(self.model.estado, self.model.FIM)
        self.controller._aplicar_entrada(self.agachar())
        self.assertEqual(self.model.estado, self.model.CONTAGEM)
        self.assertEqual((self.model.pontuacao, self.model.itens_perdidos), (0, 0))

    def test_each_new_jump_toggles_rules_and_returns_to_the_origin(self):
        for origem in (self.model.MENU, self.model.FIM):
            with self.subTest(origem=origem):
                self.model.estado = origem
                self.controller._aplicar_entrada(EntradaJogadores())
                pulo = EntradaJogadores(pulo_confirmado=True)
                self.controller._aplicar_entrada(pulo)
                self.assertEqual(self.model.estado, self.model.REGRAS)
                self.controller._aplicar_entrada(EntradaJogadores(pulo_confirmado=True, amostra_nova=False))
                self.assertEqual(self.model.estado, self.model.REGRAS)
                self.controller._aplicar_entrada(pulo)
                self.assertEqual(self.model.estado, origem)
                self.controller._aplicar_entrada(EntradaJogadores(pulo_confirmado=True, amostra_nova=False))
                self.assertEqual(self.model.estado, origem)
                self.controller._aplicar_entrada(pulo)
                self.assertEqual(self.model.estado, self.model.REGRAS)

    def test_camera_x_does_not_open_or_close_rules(self):
        for origem in (self.model.MENU, self.model.CALIBRANDO, self.model.FIM, self.model.REGRAS):
            with self.subTest(origem=origem):
                self.model.estado = origem
                self.controller._aplicar_entrada(EntradaJogadores())
                self.controller._aplicar_entrada(EntradaJogadores(bracos_x=True, x_confirmado=True))
                self.assertEqual(self.model.estado, origem)

    def test_jump_cannot_interrupt_countdown_game_or_calibration(self):
        self.model.iniciar()
        for estado in (self.model.CONTAGEM, self.model.JOGANDO, self.model.CALIBRANDO):
            with self.subTest(estado=estado):
                self.model.estado = estado
                self.controller._aplicar_entrada(EntradaJogadores(pulo_confirmado=True))
                self.assertEqual(self.model.estado, estado)

    def test_model_does_not_open_rules_outside_menu_and_results(self):
        for estado in (self.model.CONTAGEM, self.model.JOGANDO, self.model.CALIBRANDO):
            with self.subTest(estado=estado):
                self.model.estado = estado
                self.model.mostrar_regras()
                self.assertEqual(self.model.estado, estado)

    def test_stale_or_invalid_jump_does_not_toggle_rules(self):
        for origem in (self.model.MENU, self.model.FIM, self.model.REGRAS):
            for invalida in (
                {'amostra_nova': False},
                {'prontos': False},
                {'status': StatusJogadores.CRUZARAM},
                {'status': StatusJogadores.FALTA_JOGADOR},
            ):
                with self.subTest(origem=origem, invalida=invalida):
                    self.model.estado = origem
                    self.controller._aplicar_entrada(EntradaJogadores(pulo_confirmado=True, **invalida))
                    self.assertEqual(self.model.estado, origem)

    def test_escape_and_back_click_close_rules_to_their_origin(self):
        telas = Mock()
        telas.clicou_voltar.return_value = True
        input_controller = InputController(telas)
        for origem in (self.model.MENU, self.model.FIM):
            for evento in (
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20)),
            ):
                with self.subTest(origem=origem, evento=evento):
                    self.model.estado = origem
                    self.controller._aplicar_entrada(EntradaJogadores(pulo_confirmado=True))
                    self.assertEqual(self.model.estado, self.model.REGRAS)
                    input_controller.tratar_evento(evento, self.model)
                    self.assertEqual(self.model.estado, origem)

    @patch('src.config.USAR_CAMERA', False)
    def test_keyboard_space_starts_countdown_and_closes_source(self):
        source = Mock()
        source.ler.return_value = EntradaJogadores()
        self.controller.input_source = source
        self.controller.view.render = Mock(side_effect=lambda *args: setattr(self.controller, 'rodando', False))
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.controller.run()
        self.assertEqual(self.model.estado, self.model.CONTAGEM)
        source.recalibrar.assert_not_called()
        source.fechar.assert_called_once()

    @patch('src.config.USAR_CAMERA', False)
    def test_keyboard_movement_does_not_simulate_camera_gestures(self):
        source = KeyboardInput()
        teclas = set()
        with patch('pygame.key.get_pressed', return_value=Mock(__getitem__=lambda _, k: k in teclas)):
            for pressionadas, direcoes in (
                ({pygame.K_a, pygame.K_RIGHT}, (-1, 1)),
                ({pygame.K_d, pygame.K_LEFT}, (1, -1)),
                ({pygame.K_s, pygame.K_DOWN, pygame.K_x}, (0, 0)),
                (set(), (0, 0)),
            ):
                teclas.clear()
                teclas.update(pressionadas)
                entrada = source.ler()
                self.assertEqual((entrada.dir_p1, entrada.dir_p2), direcoes)
                self.assertFalse(entrada.agachamento_confirmado or entrada.x_confirmado or entrada.pulo_confirmado)

    @patch('src.config.USAR_CAMERA', False)
    def test_keyboard_rules_return_and_space_restart_after_game_over(self):
        self.model.iniciar()
        self.model.update(3)
        self.model.estado = self.model.FIM
        self.model.pontuacao = 10
        x = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x)
        self.controller.input.tratar_evento(x, self.model)
        self.assertEqual(self.model.estado, self.model.REGRAS)
        self.controller.input.tratar_evento(x, self.model)
        self.assertEqual(self.model.estado, self.model.FIM)
        self.controller.input.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE), self.model)
        self.assertEqual(self.model.estado, self.model.CONTAGEM)
        self.assertEqual(self.model.pontuacao, 0)
