"""Testa a mesma captura, detecção e calibração usadas pelo jogo."""

import argparse
import logging
import time

from src.controllers.input.camera_input import CameraInput, CameraIndisponivelError
from src.logging_config import configurar_logs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jogadores", type=int, choices=(1, 2), default=1)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    parser.add_argument("--log-file")
    args = parser.parse_args(argv)
    configurar_logs(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    entrada = None
    try:
        entrada = CameraInput(args.jogadores)
        logger.info("Teste com %d jogador(es). Pressione Q na janela para sair.", args.jogadores)
        while not entrada.erro:
            entrada.ler()
            time.sleep(0.01)
        logger.info("Teste encerrado: %s", entrada.erro)
    except CameraIndisponivelError:
        logger.exception("Nao foi possivel iniciar o teste de camera")
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo terminal")
    finally:
        if entrada is not None:
            entrada.fechar()


if __name__ == "__main__":
    main()
