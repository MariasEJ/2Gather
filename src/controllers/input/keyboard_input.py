"""Controle da dupla pelo teclado, selecionado na configuração."""

import pygame

from src.controllers.input.input_source import EntradaJogadores, InputSource
from src.vision.tipos import StatusJogadores


class KeyboardInput(InputSource):
    def ler(self):
        teclas = pygame.key.get_pressed()
        dir_p1 = int(teclas[pygame.K_d]) - int(teclas[pygame.K_a])
        dir_p2 = int(teclas[pygame.K_RIGHT]) - int(teclas[pygame.K_LEFT])
        return EntradaJogadores(
            dir_p1=dir_p1,
            dir_p2=dir_p2,
            status=StatusJogadores.OK,
            prontos=True,
        )
