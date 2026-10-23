import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from PIL import Image

from src.config import CHAO_Y, LARGURA, ALTURA, ALTURA_JOGADOR, LARGURA_JOGADOR
from src.models.falling_item import FallingItem
from src.models.lixeiras.base import Residuo
from src.models.game_model import GameModel
from src.models.player import LIXEIRAS
from src.models.fundos import FUNDOS
from src.views.game_view import GameView
from src.views.recursos_visuais import RecursosVisuais
from src.vision.tipos import StatusJogadores


class RenderizacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((LARGURA, ALTURA))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_menu_rules_countdown_game_and_result_render_with_black_band(self):
        tela = pygame.Surface((LARGURA, ALTURA))
        view = GameView(tela)
        model = GameModel()
        entrada = type('Entrada', (), {'debug': (None, type('Estado', (), {
            'status': StatusJogadores.OK, 'progresso': 1.0
        })()), 'aviso': ''})()
        for estado in (model.MENU, model.CALIBRANDO, model.REGRAS):
            model.estado = estado
            view.render(model, entrada)
            faixa = tela.subsurface((0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
            self.assertEqual(pygame.image.tobytes(faixa, 'RGB'), bytes(LARGURA * (ALTURA - CHAO_Y) * 3))
            self.assertNotEqual(tela.get_at((5, CHAO_Y - 1))[:3], (0, 0, 0))
        model.estado = model.MENU
        model.iniciar()
        for estado in (model.CONTAGEM, model.JOGANDO, model.FIM):
            model.estado = estado
            view.render(model, entrada)
            faixa = tela.subsurface((0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
            self.assertEqual(pygame.image.tobytes(faixa, 'RGB'), bytes(LARGURA * (ALTURA - CHAO_Y) * 3))
            self.assertNotEqual(tela.get_at((5, CHAO_Y - 1))[:3], (0, 0, 0))
        for jogador in model.jogadores:
            self.assertEqual((jogador.y, jogador.altura, jogador.largura),
                             (CHAO_Y - ALTURA_JOGADOR, ALTURA_JOGADOR, LARGURA_JOGADOR))

    def test_image_loading_is_cached_trimmed_scaled_and_anchored(self):
        recursos = RecursosVisuais(Path(__file__).resolve().parents[1])
        original = pygame.Surface((80, 40), pygame.SRCALPHA)
        pygame.draw.rect(original, (255, 0, 0, 255), pygame.Rect(20, 5, 40, 30))
        with patch('src.views.recursos_visuais.Path.is_file', return_value=True), \
                patch('src.views.recursos_visuais.pygame.image.load', return_value=original.copy()) as carregar:
            a = recursos.sprite('imagens/teste.png', (64, 64))
            b = recursos.sprite('imagens/teste.png', (64, 64))
            self.assertIs(a, b)
            self.assertEqual(a.get_size(), (28, 21))
            self.assertEqual(carregar.call_count, 1)
            tela = pygame.Surface((300, 200))
            retangulo = pygame.Rect(120, 80, 96, 96)
            recursos.desenhar(tela, 'imagens/teste.png', retangulo, 'centro_base')
            self.assertEqual(tela.get_at((150, 170))[:3], (255, 0, 0))

    def test_missing_image_reports_which_file_to_add(self):
        recursos = RecursosVisuais(Path(__file__).resolve().parents[1])
        with self.assertRaisesRegex(FileNotFoundError, 'missing.png'):
            recursos.sprite('imagens/missing.png', (64, 64))

    def test_every_lixeira_item_and_background_image_loads(self):
        recursos = RecursosVisuais()
        for classe in LIXEIRAS:
            with self.subTest(lixeira=classe.ID):
                self.assertGreater(recursos.sprite(classe.IMAGEM, (96, 96)).get_width(), 0)
            for item in classe.ITENS:
                with self.subTest(item=item.id):
                    self.assertGreater(recursos.sprite(item.imagem, (64, 64)).get_width(), 0)
        for fundo in FUNDOS:
            with self.subTest(fundo=fundo.ID):
                self.assertEqual(recursos.fundo(fundo.IMAGEM, (LARGURA, CHAO_Y)).get_size(), (LARGURA, CHAO_Y))

    def test_gif_background_advances_frames_and_caches_scaled_frames(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / 'animado.gif'
            recursos = RecursosVisuais(diretorio)
            quadros = [
                Image.new('RGBA', (2, 2), (255, 0, 0, 255)),
                Image.new('RGBA', (2, 2), (0, 0, 255, 255)),
            ]
            quadros[0].save(
                caminho,
                save_all=True,
                append_images=quadros[1:],
                duration=[100, 100],
                loop=0,
                disposal=2,
            )

            with patch('src.views.recursos_visuais.pygame.time.get_ticks', side_effect=(0, 100, 200)):
                primeiro = recursos.fundo('animado.gif', (4, 4))
                segundo = recursos.fundo('animado.gif', (4, 4))
                terceiro = recursos.fundo('animado.gif', (4, 4))

            self.assertEqual(primeiro.get_at((0, 0))[:3], (255, 0, 0))
            self.assertEqual(segundo.get_at((0, 0))[:3], (0, 0, 255))
            self.assertEqual(terceiro.get_at((0, 0))[:3], (255, 0, 0))
            self.assertIs(primeiro, terceiro)

    def test_gameplay_draws_only_players_and_falling_items(self):
        tela = pygame.Surface((LARGURA, ALTURA))
        view = GameView(tela)
        model = GameModel()
        model.iniciar()
        model.update(3)
        with patch.object(view.recursos, 'desenhar', wraps=view.recursos.desenhar) as desenhar:
            view.render(model)
        caminhos = [chamada.args[1] for chamada in desenhar.call_args_list]
        self.assertEqual(caminhos, [j.IMAGEM for j in model.jogadores] + [i.imagem for i in model.itens])

    def test_custom_item_size_renders_without_label_above_it(self):
        tela = pygame.Surface((LARGURA, ALTURA))
        tela.fill((70, 80, 90))
        view = GameView(tela)
        item = FallingItem(300, Residuo('pote', 'Pote', 'imagens/pote-vidro.png', (32, 52)), 'vidro', 80)
        item.y = 100
        with patch.object(view.recursos, 'desenhar', wraps=view.recursos.desenhar) as desenhar:
            view.desenhar_item(item)
        self.assertEqual(desenhar.call_args.args[2], pygame.Rect(284, 100, 32, 52))
        acima = tela.subsurface((260, 75, 80, 25))
        self.assertEqual(pygame.image.tobytes(acima, 'RGB'), bytes((70, 80, 90)) * 80 * 25)
        area_item = tela.subsurface((284, 100, 32, 52))
        self.assertNotEqual(pygame.image.tobytes(area_item, 'RGB'), bytes((70, 80, 90)) * 32 * 52)

    def test_game_over_keeps_scene_and_only_adds_title_and_score(self):
        tela = pygame.Surface((LARGURA, ALTURA))
        view = GameView(tela)
        model = GameModel()
        model.iniciar()
        model.update(3)
        model.estado, model.pontuacao = model.FIM, 12
        fundo = model.fundo
        posicoes = [(i.x, i.y) for i in model.itens]
        model.update(5)
        with patch.object(view.telas, '_texto_centralizado', wraps=view.telas._texto_centralizado) as texto, \
                patch.object(view.telas, '_painel') as painel, \
                patch.object(view.hud, 'desenhar') as hud:
            view.render(model)
        self.assertEqual([chamada.args[0] for chamada in texto.call_args_list], ['GAME OVER', 'Pontuação: 12'])
        painel.assert_not_called()
        hud.assert_not_called()
        self.assertIs(model.fundo, fundo)
        self.assertEqual([(i.x, i.y) for i in model.itens], posicoes)
        self.assertEqual(tela.get_at((20, 100)), view.recursos.fundo(fundo.IMAGEM, (LARGURA, CHAO_Y)).get_at((20, 100)))
