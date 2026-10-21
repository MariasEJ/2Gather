import itertools
import random
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from src.models.fundos import FUNDOS
from src.models.game_model import GameModel
from src.models.item_spawner import ItemSpawner
from src.models.particoes import centro_particao
from src.models.player import LIXEIRAS


class ClassesLixeirasTests(unittest.TestCase):
    def test_each_class_owns_residues_and_visual_paths(self):
        raiz = Path(__file__).resolve().parents[1]
        self.assertEqual(len(LIXEIRAS), 5)
        self.assertEqual(len({lixeira.ID for lixeira in LIXEIRAS}), 5)
        for lixeira in LIXEIRAS:
            self.assertTrue((raiz / lixeira.IMAGEM).is_file())
            self.assertGreater(len(lixeira.ITENS), 0)
            for item in lixeira.ITENS:
                self.assertTrue(item.id)
                self.assertTrue(item.imagem.startswith('imagens/'))
                self.assertTrue((raiz / item.imagem).is_file())
        self.assertEqual(len(FUNDOS), 3)
        self.assertEqual({fundo.ID for fundo in FUNDOS}, {'simples', 'Decorado', 'praia'})
        self.assertTrue(all((raiz / fundo.IMAGEM).is_file() for fundo in FUNDOS))

    def test_spawner_accepts_different_numbers_of_items(self):
        primeira, segunda = LIXEIRAS[:2]
        with patch.object(primeira, 'ITENS', primeira.ITENS[:1]), \
                patch.object(segunda, 'ITENS', segunda.ITENS[:2]):
            spawner = ItemSpawner((primeira, segunda), random.Random(3))
            gerados = [spawner.gerar() for _ in range(50)]
            self.assertEqual(
                {item.item_id for item in gerados},
                {item.id for item in primeira.ITENS + segunda.ITENS},
            )

    def test_all_ten_pairs_in_both_player_assignments(self):
        for par in itertools.permutations(LIXEIRAS, 2):
            with self.subTest(par=par):
                spawner = ItemSpawner(par, random.Random(17))
                itens = spawner.update(4000, 0)
                encontrados = set()
                faixas = {categoria.ID: set() for categoria in par}
                for item in itens:
                    encontrados.add(item.item_id)
                    self.assertIn(item.categoria_id, (par[0].ID, par[1].ID))
                    dono = 0 if item.categoria_id == par[0].ID else 1
                    self.assertIn(item.particao, range(dono, dono + 5))
                    self.assertEqual(item.x, centro_particao(item.particao))
                    faixas[item.categoria_id].add(item.particao)
                self.assertEqual(encontrados, {item.id for cls in par for item in cls.ITENS})
                self.assertEqual(faixas[par[0].ID], set(range(5)))
                self.assertEqual(faixas[par[1].ID], set(range(1, 6)))

    def test_spawner_rejects_duplicate_or_unknown_classes(self):
        for lixeiras in ((LIXEIRAS[0], LIXEIRAS[0]), (LIXEIRAS[0], str), (LIXEIRAS[0],)):
            with self.assertRaises(ValueError):
                ItemSpawner(lixeiras)

    def test_no_draw_until_confirmation_and_one_draw_per_start(self):
        rng = Mock(wraps=random.Random(17))
        decoracao = Mock(wraps=random.Random(23))
        model = GameModel(rng=rng, rng_fundo=decoracao)
        for _ in range(3):
            model.mostrar_regras()
            model.iniciar()
            model.voltar_menu()
            model.update(10)
        model.iniciar_calibracao()
        self.assertIs(type(model.p1), __import__('src.models.player', fromlist=['Lixeira']).Lixeira)
        self.assertIsNone(model.fundo)
        rng.sample.assert_not_called()
        decoracao.choice.assert_not_called()
        model.iniciar()
        self.assertEqual(model.estado, model.CONTAGEM)
        for _ in range(30):
            model.iniciar()
            model.update(0.1)
        rng.sample.assert_called_once()
        decoracao.choice.assert_called_once()
        model.estado = model.FIM
        model.mostrar_regras()
        model.voltar_menu()
        self.assertEqual(rng.sample.call_count, 1)
        model.iniciar()
        self.assertEqual(rng.sample.call_count, 2)
        self.assertEqual(decoracao.choice.call_count, 2)

    def test_countdown_freezes_controls_and_spawns_first_item_immediately(self):
        model = GameModel(rng=random.Random(1))
        model.iniciar()
        self.assertIs(type(model.p1), model.rng.sample.return_value[0] if hasattr(model.rng.sample, 'return_value') else type(model.p1))
        for numero in (3, 2, 1):
            self.assertEqual(model.numero_contagem, numero)
            self.assertEqual(model.spawner.timer, 0)
            self.assertEqual(model.itens, [])
            self.assertEqual(model.p1.x, centro_particao(2))
            model.update(1)
        self.assertEqual(model.estado, model.JOGANDO)
        self.assertEqual(len(model.itens), 1)
        self.assertEqual(model.itens[0].y, -28)
        self.assertEqual(model.spawner.timer, 0)
        primeiro = model.itens[0]
        model.update(3.99)
        self.assertEqual(len(model.itens), 1)
        model.update(0.02)
        self.assertEqual(len(model.itens), 2)
        self.assertIs(model.itens[0], primeiro)

    def test_long_frame_at_countdown_end_never_spawns_batch(self):
        model = GameModel()
        model.iniciar()
        model.update(20)
        self.assertEqual(len(model.itens), 1)
        self.assertEqual(model.spawner.timer, 0)
        self.assertEqual(model.itens_perdidos, 0)

    def test_background_does_not_change_gameplay_random_sequence(self):
        sequencias = []
        for fundo in FUNDOS:
            decoracao = Mock()
            decoracao.choice.return_value = fundo
            model = GameModel(rng=random.Random(42), rng_fundo=decoracao)
            model.iniciar()
            model.update(3)
            itens = model.itens + model.spawner.update(400, 10)
            sequencias.append([(i.item_id, i.x, i.velocidade) for i in itens])
            self.assertEqual(model.fundo, fundo)
        for sequencia in sequencias[1:]:
            self.assertEqual(sequencias[0], sequencia)

    def test_progression_is_preserved(self):
        spawner = ItemSpawner((LIXEIRAS[0], LIXEIRAS[3]))
        self.assertEqual(spawner.update(3.9, 0), [])
        self.assertEqual(len(spawner.update(0.2, 0)), 1)
        self.assertEqual(spawner.velocidade_queda, 80)
        for pontos, velocidade, intervalo in ((5, 90, 3.85), (-1, 80, 4), (10000, 420, 0.32)):
            spawner.update(0, pontos)
            self.assertEqual(spawner.velocidade_queda, velocidade)
            self.assertAlmostEqual(spawner.intervalo, intervalo)
