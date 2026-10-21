"""Converte eventos e estado do teclado em comandos do jogo."""

import pygame

from src import config

class InputController:
    def __init__(self, telas=None):
        self.telas = telas

    def tratar_evento(self, evento, model):
        if evento.type == pygame.QUIT:
            return False

        if evento.type != pygame.KEYDOWN:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.telas:
                if model.estado == model.REGRAS and self.telas.clicou_voltar(evento.pos):
                    model.voltar_menu()
            return True

        if config.USAR_CAMERA:
            if evento.key == pygame.K_ESCAPE and model.estado == model.REGRAS:
                model.voltar_menu()
            return True

        if evento.key == pygame.K_SPACE and model.estado in (model.MENU, model.FIM):
            model.iniciar()
        elif evento.key == pygame.K_x and model.estado == model.REGRAS:
            model.voltar_menu()
        elif evento.key == pygame.K_x and model.estado in (model.MENU, model.FIM):
            model.mostrar_regras()
        elif evento.key == pygame.K_ESCAPE and model.estado == model.REGRAS:
            model.voltar_menu()
        return True
