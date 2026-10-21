import unittest

from src.config import CHAO_Y
from src.models.game_model import GameModel
from src.models.falling_item import FallingItem
from src.models.player import LIXEIRAS


def lixeira(categoria_id):
    return next(classe for classe in LIXEIRAS if classe.ID == categoria_id)


def residue(item_id):
    for classe in LIXEIRAS:
        for item in classe.ITENS:
            if item.id == item_id:
                return classe, item
    raise AssertionError(item_id)


def partida():
    model = GameModel()
    model.iniciar()
    model.update(3)
    model.itens.clear()
    model.p1, model.p2 = lixeira('papel')('P1', 266), lixeira('plastico')('P2', 400)
    return model


def item_no_modelo(model, item_id, x=None, velocidade=0):
    classe, residuo = residue(item_id)
    return FallingItem(model.p1.x if x is None else x, residuo, classe.ID, velocidade)


class CapturasTests(unittest.TestCase):
    def test_all_items_score_by_category(self):
        for classe, in ((lixeira('papel'),), (lixeira('plastico'),), (lixeira('vidro'),),
                        (lixeira('metal'),), (lixeira('organico'),)):
            for residuo in classe.ITENS:
                with self.subTest(item=residuo.id):
                    model = partida()
                    model.p1 = classe('P1', 266)
                    item = FallingItem(model.p1.x, residuo, classe.ID, 0)
                    item.y = model.p1.y
                    model.itens = [item]
                    model.update(0)
                    model.update(0)
                    self.assertEqual(model.pontuacao, 1)
                    self.assertFalse(model.itens)
                    outra = lixeira('metal') if classe.ID != 'metal' else lixeira('papel')
                    model.p1 = outra('P1', 266)
                    item = FallingItem(model.p1.x, residuo, classe.ID, 0)
                    item.y = model.p1.y
                    model.itens = [item]
                    model.update(0)
                    self.assertEqual(model.pontuacao, 0)

    def test_same_lane_alone_is_not_enough(self):
        model = partida()
        model.p1.x = 275
        item = item_no_modelo(model, 'papel_jornal', 390, 80)
        item.y = 280
        model.itens = [item]
        model.update(0.1)
        self.assertEqual(model.pontuacao, 0)
        self.assertTrue(item.ativo)

    def test_adjacent_lane_cannot_capture_even_with_contact(self):
        model = partida()
        model.p1.x, model.p2.x = 399, 600
        item = item_no_modelo(model, 'papel_jornal', 401, 80)
        item.y = model.p1.y - 14
        model.itens = [item]
        model.update(0)
        self.assertEqual(model.pontuacao, 0)
        model.update(2)
        self.assertEqual(model.itens_perdidos, 1)

    def test_image_hitbox_rejects_horizontal_gaps(self):
        for item_id in ('papel_jornal', 'vidro_pote', 'metal_lata', 'organico_banana'):
            with self.subTest(item=item_id):
                model = partida()
                model.p1.x = 280
                item = item_no_modelo(model, item_id, 346, 80)
                item.y = item.y_anterior = model.p1.y
                self.assertFalse(item.toca_jogador(model.p1))
                item.x = model.p1.x
                self.assertTrue(item.toca_jogador(model.p1))

    def test_fast_items_are_caught_before_loss_for_every_category(self):
        for classe in LIXEIRAS:
            with self.subTest(categoria=classe.ID):
                model = partida()
                model.p1 = classe('P1', 266)
                item = FallingItem(model.p1.x, classe.ITENS[0], classe.ID, 1000)
                item.y = 250
                model.itens = [item]
                model.update(0.3)
                model.update(0.1)
                self.assertEqual(model.pontuacao, 1)
                self.assertEqual(model.itens_perdidos, 0)

    def test_floor_loss_only_after_top_exceeds_floor(self):
        model = partida()
        item = item_no_modelo(model, 'papel_jornal', 20, 80)
        item.y = CHAO_Y
        model.itens = [item]
        model.update(0)
        self.assertEqual(model.itens_perdidos, 0)
        model.update(0.01)
        self.assertEqual(model.itens_perdidos, 1)
        model.update(0)
        self.assertEqual(model.itens_perdidos, 1)

    def test_item_already_below_floor_is_not_caught(self):
        model = partida()
        item = item_no_modelo(model, 'papel_jornal')
        item.y = CHAO_Y + 1
        model.itens = [item]
        model.update(0)
        self.assertEqual(model.pontuacao, 0)
        self.assertEqual(model.itens_perdidos, 1)

    def test_shared_lane_prioritizes_correct_category(self):
        model = partida()
        model.p1.x, model.p2.x = 280, 376
        item = item_no_modelo(model, 'plastico_pet', 328)
        item.y = model.p1.y
        model.itens = [item]
        model.update(0)
        self.assertEqual(model.pontuacao, 1)
        self.assertFalse(model.itens)

    def test_three_losses_or_minus_five_end_round(self):
        for motivo in ('perdas', 'erros'):
            model = partida()
            for _ in range(3 if motivo == 'perdas' else 5):
                item = item_no_modelo(model, 'plastico_pet', model.p1.x, 0)
                item.y = CHAO_Y + 1 if motivo == 'perdas' else model.p1.y
                model.itens = [item]
                model.update(0)
            self.assertEqual(model.estado, model.FIM)
            self.assertEqual(model.itens_perdidos, 3 if motivo == 'perdas' else 0)
            self.assertEqual(model.pontuacao, 0 if motivo == 'perdas' else -5)
