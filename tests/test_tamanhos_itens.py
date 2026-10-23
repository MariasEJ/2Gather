import random
import unittest
from dataclasses import replace
from unittest.mock import patch

from src.models.falling_item import FallingItem
from src.models.item_spawner import ItemSpawner
from src.models.lixeiras import LixeiraMetal, LixeiraVidro, Residuo
from src.models.player import LIXEIRAS


class TamanhosItensTests(unittest.TestCase):
    def test_catalog_items_are_larger_than_previous_32_pixel_boxes(self):
        for classe in LIXEIRAS:
            for residuo in classe.ITENS:
                with self.subTest(item=residuo.id):
                    largura, altura = residuo.dimensoes
                    self.assertGreater(largura, 32)
                    self.assertGreater(altura, 32)

    def test_bottles_are_larger_than_cans_and_nail_polish(self):
        itens = {item.id: item for classe in LIXEIRAS for item in classe.ITENS}
        for garrafa in ('plastico_pet1', 'plastico_pet2'):
            for lata in ('metal_refri', 'metal_latinha'):
                with self.subTest(garrafa=garrafa, lata=lata):
                    largura, altura = itens[garrafa].dimensoes
                    largura_lata, altura_lata = itens[lata].dimensoes
                    self.assertGreater(altura, altura_lata)
                    self.assertGreater(largura * altura, largura_lata * altura_lata)
        largura, altura = itens['vidro_garrafa'].dimensoes
        largura_esmalte, altura_esmalte = itens['vidro_esmalte'].dimensoes
        self.assertGreater(altura, altura_esmalte)
        self.assertGreater(largura * altura, largura_esmalte * altura_esmalte)

    def test_spawner_preserves_each_residue_size_and_starts_above_screen(self):
        vidro = replace(LixeiraVidro.ITENS[0], tamanho=(32, 52))
        metal = replace(LixeiraMetal.ITENS[0], tamanho=(48, 20))
        with patch.object(LixeiraVidro, 'ITENS', (vidro,)), patch.object(LixeiraMetal, 'ITENS', (metal,)):
            spawner = ItemSpawner((LixeiraVidro, LixeiraMetal), random.Random(3))
            itens = [spawner.gerar() for _ in range(20)]
        self.assertEqual({item.categoria_id for item in itens}, {'vidro', 'metal'})
        for item in itens:
            largura, altura = vidro.dimensoes if item.categoria_id == 'vidro' else metal.dimensoes
            self.assertEqual(item.retangulo(), (item.x - largura / 2, -altura, largura, altura))

    def test_width_and_height_change_contact_boundaries(self):
        jogador = LixeiraVidro('P1', 300)
        for tamanho, x, y, toca in (
            ((20, 20), 370, jogador.y, False),
            ((60, 20), 370, jogador.y, True),
            ((20, 20), 300, jogador.y - 30, False),
            ((20, 40), 300, jogador.y - 30, True),
        ):
            with self.subTest(tamanho=tamanho, x=x, y=y):
                residuo = replace(LixeiraVidro.ITENS[0], tamanho=tamanho)
                item = FallingItem(x, residuo, 'vidro', 80)
                item.y = item.y_anterior = y
                self.assertEqual(item.toca_jogador(jogador), toca)

    def test_single_size_still_creates_square_area(self):
        item = FallingItem(100, replace(LixeiraVidro.ITENS[0], tamanho=36), 'vidro', 80)
        self.assertEqual(item.retangulo(), (82, -36, 36, 36))

    def test_invalid_sizes_are_rejected_at_definition(self):
        for tamanho in (0, -1, True, 1.5, (28,), (28, 0), (28, -5), (28, 2.5), (1, 2, 3)):
            with self.subTest(tamanho=tamanho), self.assertRaises(ValueError):
                Residuo('vidro', 'Vidro', 'imagens/pote-vidro.png', tamanho)
