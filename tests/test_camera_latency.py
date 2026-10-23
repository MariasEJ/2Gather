import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from src.vision.camera_worker import CameraWorker


class CameraLatencyTests(unittest.TestCase):
    def test_capture_continues_during_inference_and_discards_older_frames(self):
        inferindo = threading.Event()
        capturou_mais = threading.Event()
        liberar = threading.Event()
        terminou = threading.Event()
        processados = []
        contador = 0

        def ler():
            nonlocal contador
            contador += 1
            if contador == 2:
                inferindo.wait(2)
            if contador > 4:
                capturou_mais.set()
                worker._parar.wait(2)
                return False, None
            return True, np.full((2, 2, 3), contador, dtype=np.uint8)

        def detectar(frame):
            processados.append(int(frame[0, 0, 0]))
            if len(processados) == 1:
                inferindo.set()
                liberar.wait(2)
            else:
                terminou.set()
            return [], frame

        cap = Mock()
        cap.read.side_effect = ler
        cv = SimpleNamespace(VideoCapture=lambda _: cap, flip=lambda f, _: f,
                             CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4, CAP_PROP_BUFFERSIZE=38)
        detector = Mock(detectar_e_desenhar=Mock(side_effect=detectar))
        worker = CameraWorker(cv, lambda: detector)
        worker.start()
        try:
            self.assertTrue(inferindo.wait(1))
            self.assertTrue(capturou_mais.wait(0.5), 'Captura ficou bloqueada na inferência')
            self.assertEqual(int(worker.ultimo_frame()[1][0, 0, 0]), 4)
            liberar.set()
            self.assertTrue(terminou.wait(1))
            self.assertEqual(processados[:2], [1, 4])
        finally:
            liberar.set()
            worker.parar()
        self.assertFalse(worker.is_alive())
        cap.release.assert_called_once()
        detector.fechar.assert_called_once()
