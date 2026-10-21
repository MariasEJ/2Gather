"""Seleção única de entrada; bibliotecas de câmera são importadas sob demanda."""

from src import config


def criar_fonte_entrada():
    if config.USAR_CAMERA:
        from src.controllers.input.camera_input import CameraInput
        return CameraInput()
    from src.controllers.input.keyboard_input import KeyboardInput
    return KeyboardInput()
