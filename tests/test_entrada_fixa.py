import os
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from src.controllers.input import criar_fonte_entrada
from src.controllers.input.keyboard_input import KeyboardInput


class EntradaFixaTests(unittest.TestCase):
    def test_keyboard_does_not_import_or_initialize_camera_dependencies(self):
        codigo = '''
import sys
sys.modules['mediapipe'] = None
sys.modules['cv2'] = None
from src import config
config.USAR_CAMERA = False
import main
from src.controllers.input import criar_fonte_entrada
from src.controllers.input.keyboard_input import KeyboardInput
assert isinstance(criar_fonte_entrada(), KeyboardInput)
assert 'src.controllers.input.camera_input' not in sys.modules
'''
        resultado = subprocess.run([sys.executable, '-c', codigo], capture_output=True,
                                   text=True, timeout=15)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)

    def test_config_is_the_only_mode_selector(self):
        with patch('src.config.USAR_CAMERA', False):
            self.assertIsInstance(criar_fonte_entrada(), KeyboardInput)
        with patch('src.config.USAR_CAMERA', True), \
                patch('src.controllers.input.camera_input.CameraInput') as camera:
            self.assertIs(criar_fonte_entrada(), camera.return_value)
            camera.assert_called_once_with()

    def test_removed_command_line_options_are_rejected(self):
        import main
        for argumentos in (['--input', 'teclado'], ['--jogadores', '1']):
            with patch('sys.stderr'), self.assertRaises(SystemExit) as erro:
                main.main(argumentos)
            self.assertEqual(erro.exception.code, 2)

    def test_main_closes_source_even_when_controller_fails(self):
        import main
        source = Mock()
        with patch.object(main, 'criar_fonte_entrada', return_value=source), \
                patch.object(main, 'GameController', side_effect=RuntimeError('simulado')), \
                patch.object(main, 'configurar_logs'), \
                patch.object(main.pygame, 'init'), patch.object(main.pygame, 'quit') as fechar, \
                patch.object(main.pygame.display, 'set_mode'), \
                self.assertLogs('catch_duo', level='ERROR'), self.assertRaises(RuntimeError):
            main.main([])
        source.fechar.assert_called_once()
        fechar.assert_called_once()
