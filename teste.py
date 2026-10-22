"""Teste individual: execute python teste.py na raiz usando a .venv do projeto.

Fique em pé com quadris e pés visíveis até concluir a calibração.
O terminal imprime pulo, agachar, direita e esquerda. R recalibra; Q/ESC sai.
"""

import time
from collections import deque
from statistics import mean

import cv2
import mediapipe as mp

from src.config import (
    AMOSTRAS_CALIBRACAO, CAMERA_TIMEOUT_INICIAL, CAMERA_TIMEOUT_QUADRO,
    CONFIANCA_GESTOS, INTERVALO_MAX_AMOSTRAS_PULO, OSCILACAO_CALIBRACAO,
    TEMPO_ESTABILIDADE,
)
from src.vision.camera_worker import CameraWorker
from src.vision.gestos import DetectorPulo, esta_agachado
from src.vision.pose_detector import PoseDetector


JANELA = '2Gather - teste individual'
LIMIAR_DESLOCAMENTO = 0.03  


class PoseIndividual:
    """Mesma pose do jogo, aplicada uma única vez à imagem inteira."""

    def __init__(self):
        if not hasattr(mp, 'solutions'):
            raise RuntimeError('MediaPipe Solutions indisponível. Use a .venv do projeto.')
        self.pose = PoseDetector._criar_pose()

    def detectar_e_desenhar(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        resultado = self.pose.process(rgb)
        anotado = frame.copy()
        pessoas = []
        if resultado.pose_landmarks is not None:
            largura = frame.shape[1]
            pessoa = PoseDetector._extrair_pessoa(
                resultado.pose_landmarks.landmark, frame, 0, largura, largura,
            )
            if pessoa is not None:
                pessoas.append(pessoa)
            mp.solutions.drawing_utils.draw_landmarks(
                anotado, resultado.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS,
            )
        return pessoas, anotado

    def fechar(self):
        self.pose.close()


class LeitorMovimentos:
    def __init__(self):
        self.recalibrar()

    def recalibrar(self):
        self.baseline_hip_y = self.baseline_foot_y = None
        self._amostras = deque(maxlen=AMOSTRAS_CALIBRACAO)
        self._inicio_calibracao = self._ultimo_tempo = None
        self._centro_x = None
        self._agachado = False
        self._pulo = DetectorPulo()
        self.status = 'Fique em pe, parado, com quadris e pes visiveis'

    @property
    def calibrado(self):
        return self.baseline_hip_y is not None

    def _interromper_movimento(self):
        self._pulo.reset_movimento()
        self._centro_x = None
        self._agachado = False
        self._amostras.clear()
        self._inicio_calibracao = None

    def atualizar(self, pessoa, agora):
        if self._ultimo_tempo is not None:
            if agora <= self._ultimo_tempo:
                return []
            if agora - self._ultimo_tempo > INTERVALO_MAX_AMOSTRAS_PULO:
                self._interromper_movimento()
        self._ultimo_tempo = agora
        if pessoa is None or pessoa.confianca_quadris < CONFIANCA_GESTOS:
            self._interromper_movimento()
            self.status = 'Sem pose confiavel: enquadre o corpo e ilumine o ambiente'
            return []

        if not self.calibrado:
            if pessoa.foot_y is None:
                self._interromper_movimento()
                self.status = 'Enquadre os dois pes e os quadris para calibrar'
                return []
            amostra = (pessoa.hip_y, pessoa.foot_y)
            if self._amostras and any(
                max(v[i] for v in (*self._amostras, amostra))
                - min(v[i] for v in (*self._amostras, amostra)) > OSCILACAO_CALIBRACAO
                for i in range(2)
            ):
                self._amostras.clear()
                self._inicio_calibracao = None
            if self._inicio_calibracao is None:
                self._inicio_calibracao = agora
            self._amostras.append(amostra)
            self.status = f'Calibrando {len(self._amostras)}/{AMOSTRAS_CALIBRACAO}: fique em pe e parado'
            if (len(self._amostras) < AMOSTRAS_CALIBRACAO
                    or agora - self._inicio_calibracao < TEMPO_ESTABILIDADE):
                return []
            self.baseline_hip_y = mean(p[0] for p in self._amostras)
            self.baseline_foot_y = mean(p[1] for p in self._amostras)
            self._centro_x = pessoa.cx

        self.status = ('Pronto: pule, agache ou mova-se para os lados'
                       if pessoa.foot_y is not None else 'Pes fora da imagem: pulo indisponivel')
        movimentos = []
        if self._pulo.atualizar(pessoa.hip_y, pessoa.foot_y, self.baseline_hip_y,
                               self.baseline_foot_y, agora, pessoa.confianca_quadris):
            movimentos.append('pulo')
        agachado = esta_agachado(pessoa.hip_y, self.baseline_hip_y, pessoa.confianca_quadris)
        if agachado and not self._agachado:
            movimentos.append('agachar')
        self._agachado = agachado

        # A referência acompanha o deslocamento: voltar à esquerda também
        # funciona quando a pessoa ainda está na metade direita da imagem.
        if self._centro_x is not None:
            deslocamento = pessoa.cx - self._centro_x
            if abs(deslocamento) >= LIMIAR_DESLOCAMENTO:
                movimentos.append('direita' if deslocamento > 0 else 'esquerda')
                self._centro_x = pessoa.cx
        else:
            self._centro_x = pessoa.cx
        return movimentos


def main():
    leitor = LeitorMovimentos()
    worker = CameraWorker(detector_factory=PoseIndividual)
    janela_aberta = False
    ultimo_timestamp = None
    ultimo_movimento = '-'
    inicio = time.monotonic()
    print('Teste para UMA pessoa. Fique em pé e parado, com quadris e pés visíveis.', flush=True)
    print('Imagem espelhada: direita/esquerda seguem seu movimento na tela.', flush=True)
    print('Na janela da câmera: R recalibra; Q ou ESC encerra.', flush=True)
    try:
        cv2.namedWindow(JANELA, cv2.WINDOW_NORMAL)
        janela_aberta = True
        worker.start()
        while True:
            if worker.erro:
                print(f'Erro: {worker.erro}', flush=True)
                return 1
            quadro = worker.ultimo()
            agora = time.monotonic()
            if ((quadro is None and agora - inicio > CAMERA_TIMEOUT_INICIAL)
                    or (quadro is not None and agora - quadro.timestamp_ms / 1000 > CAMERA_TIMEOUT_QUADRO)):
                print('Erro: a câmera não está fornecendo quadros novos.', flush=True)
                return 1
            if quadro is not None:
                if quadro.timestamp_ms != ultimo_timestamp:
                    ultimo_timestamp = quadro.timestamp_ms
                    estava_calibrado = leitor.calibrado
                    pessoa = quadro.pessoas[0] if quadro.pessoas else None
                    movimentos = leitor.atualizar(pessoa, quadro.timestamp_ms / 1000)
                    if leitor.calibrado and not estava_calibrado:
                        print('Calibração concluída. Pode testar os movimentos.', flush=True)
                    for movimento in movimentos:
                        print(movimento, flush=True)
                    if movimentos:
                        ultimo_movimento = ' + '.join(movimentos)
                frame = quadro.frame_bgr.copy()
                for linha, texto in enumerate((leitor.status, f'Ultimo: {ultimo_movimento}',
                                                'R: recalibrar | Q/ESC: sair')):
                    cv2.putText(frame, texto, (10, 25 + linha * 25), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 255, 255), 1, cv2.LINE_AA)
                cv2.imshow(JANELA, frame)
            tecla = cv2.waitKey(16) & 0xFF
            if tecla in (ord('q'), ord('Q'), 27) or cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:
                break
            if tecla in (ord('r'), ord('R')):
                leitor.recalibrar()
                ultimo_movimento = '-'
                print('Recalibrando: fique em pé e parado, com os pés visíveis.', flush=True)
    except KeyboardInterrupt:
        print('\nTeste encerrado.', flush=True)
    except cv2.error as exc:
        print(f'Erro na janela da câmera: {exc}', flush=True)
        return 1
    finally:
        worker.parar()
        if janela_aberta:
            try:
                cv2.destroyWindow(JANELA)
            except cv2.error:
                pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
