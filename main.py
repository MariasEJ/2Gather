"""Ponto de entrada do Catch Duo."""

import pygame

from src.config import ALTURA, LARGURA
from src.controllers.game_controller import GameController


def main():
    pygame.init()
    try:
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        controller = GameController(tela)
        controller.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
