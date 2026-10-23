"""Benchmark reproduzível: câmera simulada a 30 FPS e inferência de 80 ms.

Execute python -m scripts.medir_latencia_camera. Não abre a webcam.
A idade mede desde a produção simulada da imagem até o fim da inferência.
"""

import statistics
import time
from types import SimpleNamespace

import numpy as np

from src.vision.camera_worker import CameraWorker


def medir(amostras=24):
    class Captura:
        def __init__(self):
            self.inicio = time.perf_counter()
            self.frames = 0

        def isOpened(self):
            return True

        def set(self, *_):
            return True

        def read(self):
            self.frames += 1
            produzido = self.inicio + self.frames / 30
            time.sleep(max(0, produzido - time.perf_counter()))
            return True, np.full((1, 1, 3), produzido)

        def release(self):
            pass

    idades = []

    class Detector:
        def detectar_e_desenhar(self, frame):
            time.sleep(0.08)
            idades.append((time.perf_counter() - frame[0, 0, 0]) * 1000)
            if len(idades) >= amostras:
                worker._parar.set()
            return [], frame

        def fechar(self):
            pass

    captura = Captura()
    cv = SimpleNamespace(VideoCapture=lambda _: captura, flip=lambda frame, _: frame,
                         CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4, CAP_PROP_BUFFERSIZE=38)
    worker = CameraWorker(cv, Detector)
    inicio = time.perf_counter()
    worker.start()
    worker.join(timeout=10)
    worker.parar()
    if worker.erro or len(idades) != amostras:
        raise RuntimeError(worker.erro or 'Benchmark não terminou no prazo')
    duracao = time.perf_counter() - inicio
    return {'fps_captura': round(captura.frames / duracao, 1),
            'fps_inferencia': round(len(idades) / duracao, 1),
            'idade_media_ms': round(statistics.mean(idades), 1),
            'idade_maxima_ms': round(max(idades), 1)}


if __name__ == '__main__':
    for rodada in range(3):
        print(f'Rodada {rodada + 1}: {medir()}', flush=True)
