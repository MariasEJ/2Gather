import argparse
import logging
import sys

import pygame

from src.config import ALTURA, LARGURA
from src.controllers.input.camera_input import CameraInput
from src.controllers.input.camera_input import CameraIndisponivelError
from src.controllers.input.keyboard_input import KeyboardInput
from src.controllers.game_controller import GameController
from src.logging_config import configurar_logs

#  1 ou 2 
NUM_JOGADORES = 1

# Mude para False para jogar no teclado sem inicializar a câmera.
USAR_CAMERA = True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Catch Duo: controle por corpo ou teclado")
    parser.add_argument("--input", choices=("camera", "teclado"),
                        default="camera" if USAR_CAMERA else "teclado")
    parser.add_argument("--jogadores", type=int, choices=(1, 2), default=NUM_JOGADORES)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    parser.add_argument("--log-file", help="Também salva os logs neste arquivo")
    args = parser.parse_args(argv)
    configurar_logs(args.log_level, args.log_file)
    logger = logging.getLogger("catch_duo")
    if args.jogadores not in (1, 2):
        raise ValueError("NUM_JOGADORES deve ser 1 ou 2")
    logger.info("Iniciando: entrada=%s jogadores=%d Python=%s executavel=%s",
                args.input, args.jogadores, sys.version.split()[0], sys.executable)
    pygame.init()
    try:
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        if args.input == "camera":
            try:
                fonte_entrada = CameraInput(args.jogadores)
            except CameraIndisponivelError as exc:
                logger.warning("%s Usando teclado como alternativa.", exc)
                fonte_entrada = KeyboardInput(args.jogadores)
        else:
            fonte_entrada = KeyboardInput(args.jogadores)

        try:
            controller = GameController(tela, fonte_entrada, args.jogadores)
            controller.run()
        finally:
            fonte_entrada.fechar()
    except Exception:
        logger.exception("Erro fatal no jogo")
        raise
    finally:
        pygame.quit()
        logger.info("Jogo encerrado")


if __name__ == "__main__":
    main()
