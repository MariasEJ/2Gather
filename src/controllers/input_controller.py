"""Converte eventos e estado do teclado em comandos do jogo."""

import pygame


class InputController:
    def __init__(self, telas=None):
        self.telas = telas

    def ler_direcoes(self):
        teclas = pygame.key.get_pressed()
        dir_p1 = int(teclas[pygame.K_d]) - int(teclas[pygame.K_a])
        dir_p2 = int(teclas[pygame.K_RIGHT]) - int(teclas[pygame.K_LEFT])
        return dir_p1, dir_p2

    def tratar_evento(self, evento, model):
        if evento.type == pygame.QUIT:
            return False

        if evento.type != pygame.KEYDOWN:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.telas:
                if model.estado == model.MENU:
                    acao = self.telas.acao_botao_menu(evento.pos)
                    if acao == "iniciar":
                        model.iniciar()
                    elif acao == "regras":
                        model.mostrar_regras()
                elif model.estado == model.REGRAS and self.telas.clicou_voltar(evento.pos):
                    model.voltar_menu()
            return True

        if evento.key == pygame.K_SPACE and model.estado == model.MENU:
            model.iniciar()
        elif evento.key == pygame.K_r and model.estado == model.MENU:
            model.mostrar_regras()
        elif evento.key == pygame.K_ESCAPE and model.estado == model.REGRAS:
            model.voltar_menu()
        elif evento.key in (pygame.K_p, pygame.K_ESCAPE):
            model.alternar_pausa()
        elif evento.key == pygame.K_r and model.estado == model.FIM:
            model.reset()
            model.iniciar()
        return True
