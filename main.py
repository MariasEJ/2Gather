import argparse
import logging
import sys

import pygame

from src import config
from src.controllers.input import criar_fonte_entrada
from src.controllers.game_controller import GameController
from src.logging_config import configurar_logs


def main(argv=None):
    parser = argparse.ArgumentParser(description='2Gather: jogo cooperativo para duas pessoas')
    parser.add_argument('--log-level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR'), default='INFO')
    parser.add_argument('--log-file', help='Também salva os logs neste arquivo')
    args = parser.parse_args(argv)
    configurar_logs(args.log_level, args.log_file)
    logger = logging.getLogger('catch_duo')
    logger.info('Iniciando: entrada=%s jogadores=2 Python=%s executavel=%s',
                'camera' if config.USAR_CAMERA else 'teclado', sys.version.split()[0], sys.executable)
    pygame.init()
    fonte_entrada = None
    try:
        tela = pygame.display.set_mode((config.LARGURA, config.ALTURA))
        fonte_entrada = criar_fonte_entrada()
        controller = GameController(tela, fonte_entrada)
        controller.run()
    except Exception:
        logger.exception('Erro fatal no jogo')
        raise
    finally:
        if fonte_entrada is not None:
            fonte_entrada.fechar()
        pygame.quit()
        logger.info('Jogo encerrado')


if __name__ == '__main__':
    main()
