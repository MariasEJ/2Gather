"""Logs legíveis no terminal e, opcionalmente, em arquivo."""

import logging


def configurar_logs(nivel="INFO", arquivo=None):
    handlers = [logging.StreamHandler()]
    if arquivo:
        handlers.append(logging.FileHandler(arquivo, encoding="utf-8"))
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
