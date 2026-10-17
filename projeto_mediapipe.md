# Catch Duo v2 – Controle por câmera (MediaPipe + OpenCV)

Atualização do projeto anterior (`PROJETO_JOGO.md`). **As regras do jogo não mudam.** O que muda é a **fonte de controle**: em vez do teclado, uma câmera aponta para os dois jogadores e o corpo de cada um move o seu triângulo.

Resumo das novidades:

1. Câmera + MediaPipe detectam **duas pessoas** ao mesmo tempo.
2. O sistema decide quem é **P1 (esquerda)** e quem é **P2 (direita)** e acompanha cada um ao longo da partida.
3. A posição do corpo na câmera vira a posição do triângulo na tela.
4. Se os jogadores **trocarem de lado** (ou alguém sair do campo da câmera), o jogo **pausa sozinho** e só volta quando os dois reassumirem a posição inicial.
5. O teclado continua funcionando como modo alternativo (ótimo para testar sem câmera).

### Correções da implementação em 17/10/2026

- Referência local analisada: `HerPules/pose_detector.py` e
  `HerPules/input_providers.py`, com Solutions Pose, imagem espelhada e controle
  derivado dos quadris. Os trechos abaixo são esboços; o código em `src/` é a implementação.
- Corrigida a transição `CALIBRANDO -> JOGANDO`: `GameModel.iniciar()` precisa
  aceitar `CALIBRANDO`, inclusive no modo teclado.
- A pose completa é desenhada, mas apenas os dois quadris visíveis e dentro da
  imagem são necessários para controlar. `CONFIANCA_QUADRIS` é independente da
  confiança de detecção MediaPipe. Cabeça/pés ausentes não impedem calibrar.
- Falhas breves respeitam a tolerância de quadros; ausência prolongada pausa e
  exige nova calibração. Quadros repetidos não avançam a calibração. Uma captura
  travada ou erro de inferência ativa o teclado; ausência de pessoas com câmera
  funcionando mantém a espera por reposicionamento.
- Captura e MediaPipe pertencem à thread de câmera; a janela OpenCV é atualizada
  no loop principal. `Q` libera a entrada de câmera e ativa o teclado.
- As metades da imagem têm limite visual. Este modo exige uma pessoa por região;
  não oferece detecção multipessoa irrestrita quando ambas ocupam a mesma metade.
- Logs no terminal mostram visibilidade dos quadris, motivo de rejeição, FPS,
  progresso, estados, pontuação e exceções. `--log-file` permite guardar a sessão.
- Testes de regressão: `.venv/bin/python -m unittest discover -s tests -v`.

## Revisão do plano: câmera em janela própria e rastreamento corporal completo

Esta revisão atende ao pedido de 17/10/2026 e substitui as instruções antigas de miniatura dentro da tela do jogo e de detecção limitada ao tronco. O plano foi atualizado antes da implementação; o código agora segue as decisões abaixo.

### O que foi observado em `ttea-main`

- O módulo `games/kartea/` contém modelos e configuração do jogo. A captura e visualização de pose ficam em módulos compartilhados, como `core/cameravideothread.py` e `games/herpules2/pose_detector.py`.
- `herpules2/pose_detector.py` usa `mp.solutions.pose.Pose`, obtém os landmarks corporais e desenha a pose completa com `mp_drawing.draw_landmarks`; a entrada do jogo atualiza a janela OpenCV separada com `cv2.imshow`.
- `herpules2/input_providers.py` transforma coordenadas corporais em comandos do jogo, calculando pontos médios dos quadris e tornozelos para detectar movimentos verticais. A analogia para este jogo é converter o deslocamento horizontal do corpo em uma posição X do jogador.
- KARTea orienta o comportamento e a apresentação do carro, mas a implementação de rastreamento corporal que pode ser reaproveitada como referência está nos componentes compartilhados e no `herpules2`.

### Decisões de implementação

1. **Janela de câmera independente:** mostrar a imagem espelhada e os landmarks em uma janela OpenCV separada da janela Pygame. Remover o preview embutido do `GameView` e o desenho da miniatura no HUD/campo de jogo. Atualizar `imshow`/`waitKey` no loop principal, como a entrada de câmera do exemplo, e manter captura/inferência na thread de fundo.
2. **Corpo inteiro:** usar `mp.solutions.pose.Pose` e renderizar as conexões do esqueleto completo (rosto, ombros, braços, tronco, quadris, pernas e pés) sobre o frame da câmera. Configurar `model_complexity` e resolução para priorizar a detecção dos pés sem tornar o loop do jogo lento.
3. **Movimento lateral:** calcular o centro horizontal a partir do ponto médio dos quadris (com opção de combinar ombros/quadris) e mapear sua posição normalizada para a coordenada X do jogador na tela. Usar suavização para reduzir tremores. A movimentação é contínua: corpo à esquerda move o personagem à esquerda; corpo à direita move o personagem à direita.
4. **Uma ou duas pessoas:** preservar `NUM_JOGADORES` em `main.py`. Para duas pessoas com a API Solutions (uma pose por chamada), processar uma região por jogador, converter landmarks de volta às coordenadas do frame completo e desenhar ambos os esqueletos na janela de câmera. Validar que os corpos inteiros cabem nas respectivas regiões; se a divisão cortar cabeça ou pés, rever câmera/resolução/áreas de interesse durante a implementação.
5. **Thread e encerramento:** a thread de câmera continua sendo dona de `VideoCapture` e das instâncias MediaPipe. O `CameraInput.ler`, chamado pelo loop principal, atualiza a janela OpenCV com `imshow`/`waitKey`; ao fechar a janela, sinaliza o fallback e fecha câmera e pose. Não abrir outra captura da webcam.
6. **Falhas:** se a câmera não abrir, a pose não for detectada ou a janela for fechada, comunicar o estado ao `CameraInput` e preservar o fallback para teclado existente. Definir na implementação o comportamento consistente ao fechar a janela da câmera (encerrar a entrada da câmera e trocar para teclado, sem travar a partida).

### Arquivos que devem mudar ao implementar

| Arquivo | Mudança prevista |
|---|---|
| `src/vision/pose_detector.py` | Retornar landmarks completos e desenhar o esqueleto de cada jogador; calcular centro X corporal com confiança/visibilidade. |
| `src/vision/camera_worker.py` | Capturar, inferir, publicar frame anotado/coordenadas e fechar câmera/pose com segurança. |
| `src/controllers/input/camera_input.py` | Criar/atualizar/fechar a janela OpenCV no loop principal; tratar `Q` e fechamento pelo gerenciador de janelas. |
| `src/vision/tipos.py` | Expandir dados do frame para carregar landmarks ou frame anotado e estado de janela sem importar Pygame. |
| `src/controllers/input/camera_input.py` | Usar o centro X do corpo para produzir os alvos horizontais dos jogadores; manter suavização e fallback. |
| `src/vision/mapeamento.py` | Mapear X do corpo para X da tela e ajustar faixa/sensibilidade conforme a calibração. |
| `src/views/camera_preview_view.py` | Remover quando o preview embutido deixar de ser referenciado. |
| `src/views/game_view.py` e `src/controllers/game_controller.py` | Remover o preview integrado e manter a janela principal dedicada ao jogo. |
| `src/config.py` | Adicionar/ajustar janela/resolução, complexidade do modelo, visibilidade mínima, centro de controle e suavização. |
| `README.md` e `GUIA_CONFIGURACAO.md` | Documentar janela independente, enquadramento de corpo inteiro, controle lateral e configurações. |

### Critérios para considerar a implementação pronta

- Ao iniciar o modo câmera, aparecem duas janelas independentes: jogo e webcam anotada.
- A janela da webcam mostra o corpo inteiro e o esqueleto acompanha cabeça e pés, não apenas o tronco.
- Mover o corpo lateralmente desloca o personagem/jogador na mesma direção, com pouco tremor e sem saltos bruscos.
- A configuração de um jogador segue funcionando; no modo de dois jogadores, cada corpo controla seu próprio personagem e ambos aparecem na visualização.
- Fechar a janela da câmera ou desconectar o dispositivo não trava o Pygame; a entrada alterna para teclado conforme o fluxo atual.
- As instruções explicam distância/enquadramento necessários para manter cabeça e pés visíveis.

### Verificação manual planejada

1. Iniciar com `NUM_JOGADORES = 1`; confirmar a janela OpenCV separada e a detecção desde a cabeça até os pés.
2. Mover tronco/quadris para esquerda e direita; confirmar que o jogador acompanha o sentido e que a suavização não cria atraso excessivo.
3. Repetir com `NUM_JOGADORES = 2`, posicionando uma pessoa em cada lado; confirmar esqueleto e controle independentes.
4. Fechar a janela da câmera e desconectar/reconectar o dispositivo; confirmar encerramento limpo e fallback de teclado.

---

## 1. Bibliotecas e uma decisão importante

| Biblioteca | Para quê |
|---|---|
| `opencv-contrib-python` | Distribuição OpenCV requerida pelo MediaPipe; fornece `cv2` para webcam, conversão e preview. |
| `mediapipe` | Detectar o corpo usando `mp.solutions.pose`. |
| `numpy` | Dependência dos dois acima; usado para converter frames em imagem do pygame. |

> **Decisão atual:** usar somente as bibliotecas definidas para o projeto e a API `mp.solutions.pose`, sem Pose Landmarker/Tasks API e sem download de modelo.
> Essa API processa uma pessoa por chamada. No modo de dois jogadores, dividir o quadro em metades e processar cada metade com uma instância `Pose` independente permite detectar uma pessoa em cada lado.

- A versão `mediapipe==0.10.21` oferece essa API e publica wheels para Python até 3.12; configure o ambiente virtual com Python 3.12 ou anterior.

---

## 2. Como funciona a ideia (visão geral)

```
 Câmera ─► CameraWorker (thread)          ┌───────────────────────────────┐
           │  frame → espelha → MediaPipe │  vision/ (nova camada)        │
           ▼                              │  PoseDetector  → pessoas      │
     QuadroVisao (pessoas + frame)        │  PlayerTracker → quem é quem  │
           │                              └───────────────────────────────┘
           ▼
    CameraInput (InputSource)  ──► EntradaJogadores(alvo_x P1, alvo_x P2, status, prontos)
           │
           ▼
     GameController ──► GameModel (move os triângulos, pausa/retoma) ──► GameView (janela do jogo)

Em paralelo, o `CameraWorker` captura e processa frames; o loop principal exibe o frame espelhado e os esqueletos completos em uma janela OpenCV independente.
```

Onde isso se encaixa no MVC:

- **Model**: continua com as regras. Ganha dois estados novos (`CALIBRANDO`, `PAUSADO_POSICAO`) e passa a aceitar uma posição-alvo (`alvo_x`) além de direção.
- **View**: mantém a janela Pygame para jogo e mensagens de calibração. A câmera é exibida em uma janela OpenCV independente, atualizada por `CameraInput` no loop principal.
- **Controller**: a câmera é um **dispositivo de entrada**, então toda a parte de visão fica na camada de controle, atrás de uma interface comum com o teclado (`InputSource`).

---

## 3. Fluxo de estados do jogo

```
MENU ──ESPAÇO──► CALIBRANDO ──posições OK por 1 s──► JOGANDO ──tempo acabou──► FIM
                     ▲                                  │  ▲                      │
                     │                       cruzaram / │  │ posições OK por 1 s  │
                     │                      faltou gente▼  │                      │
                     │                          PAUSADO_POSICAO                   │
                     └─────────────────────── R (reiniciar) ◄─────────────────────┘

JOGANDO ◄──► PAUSADO   (tecla P, pausa manual – continua existindo)
```

- No **modo teclado**, `CALIBRANDO` passa instantaneamente (o `KeyboardInput` sempre diz "tudo certo"), então o fluxo é o mesmo nos dois modos.
- Durante `PAUSADO_POSICAO` o `GameModel.update()` não faz nada (o estado não é `JOGANDO`), então **itens e cronômetro ficam congelados**, como já acontece na pausa normal.

---

## 4. Estrutura de pastas (o que é novo / alterado)

```
catch_duo/
├── main.py                              [ALTERADO]  escolhe teclado ou câmera
├── requirements.txt                     [ALTERADO]  + OpenCV, mediapipe, numpy
├── README.md                            [ALTERADO]  instruções de câmera
├── scripts/
│   └── testar_camera.py                 [NOVO]  janela OpenCV para testar luz/distância
├── src/
│   ├── config.py                        [ALTERADO]
│   ├── models/
│   │   ├── player.py                    [ALTERADO]  ganha alvo_x
│   │   └── game_model.py                [ALTERADO]  novos estados + movimento por alvo
│   ├── views/
│   │   ├── game_view.py                 [ALTERADO]  remove o preview da câmera
│   │   └── screens_view.py              [ALTERADO]  telas de calibração e de reposicionar
│   ├── controllers/
│   │   ├── game_controller.py           [ALTERADO]
│   │   └── input/
│   │       ├── __init__.py
│   │       ├── input_source.py          [NOVO]  interface + EntradaJogadores
│   │       ├── keyboard_input.py        [NOVO]  (antigo input_controller.py)
│   │       └── camera_input.py          [NOVO]
│   └── vision/                          [NOVO – sem nada de pygame]
│       ├── __init__.py
│       ├── tipos.py
│       ├── camera_worker.py
│       ├── pose_detector.py
│       ├── player_tracker.py
│       └── mapeamento.py
└── tests/
    ├── test_player_tracker.py           [NOVO]
    ├── test_mapeamento.py               [NOVO]
    ├── test_model_alvo.py               [NOVO]
    ├── test_player_movement.py          (já existe)
    ├── test_scoring.py                  (já existe)
    └── test_spawner.py                  (já existe)
```

Regra de ouro: `src/vision/` **só** conhece OpenCV/MediaPipe e dados simples. `src/models/` continua sem importar OpenCV nem MediaPipe.

---

## 5. Camada de visão (`src/vision/`)

### `tipos.py`
Estruturas de dados que circulam entre os módulos.

```python
@dataclass
class PessoaDetectada:
    cx: float            # centro horizontal dos quadris, 0.0 (esq) a 1.0 (dir), JÁ ESPELHADO
    cy: float            # centro vertical dos quadris, 0.0 a 1.0
    tamanho: float       # largura dos ombros (ajuda a distinguir as pessoas)
    cor: tuple | None    # cor média da camisa (H, S, V) – ajuda a não trocar as identidades

@dataclass
class QuadroVisao:
    pessoas: list[PessoaDetectada]
    frame_bgr: ndarray | None    # imagem espelhada e anotada, exibida na janela OpenCV
    timestamp_ms: int

class StatusJogadores(Enum):
    OK = "ok"
    FALTA_JOGADOR = "falta_jogador"
    CRUZARAM = "cruzaram"
    REPOSICIONANDO = "reposicionando"   # aguardando voltar à posição inicial

@dataclass
class EstadoJogadores:
    p1_cx: float | None
    p2_cx: float | None
    status: StatusJogadores
    prontos: bool       # True quando os dois estão na posição inicial há tempo suficiente
```

### `camera_worker.py`
Roda a câmera e o MediaPipe em uma **thread separada**, para o jogo continuar a 60 FPS mesmo que a detecção seja mais lenta (~20–30 FPS).

```python
class CameraWorker(threading.Thread):
    def __init__(self, indice=CAMERA_INDICE):
        self._lock = threading.Lock()
        self._ultimo = None
        self._rodando = True
        self.daemon = True

    def run(self):
        cap = cv2.VideoCapture(CAMERA_INDICE)
        cap.set(CAP_PROP_FRAME_WIDTH, 640); cap.set(CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened(): self._erro = "Câmera indisponível"; return

        detector = PoseDetector()          # criado DENTRO da thread (objetos do MediaPipe não são thread-safe)
        while self._rodando:
            ok, frame = cap.read()
            if not ok: continue
            frame = cv2.flip(frame, 1)     # espelha: o que está à esquerda na tela é a esquerda do jogador
            pessoas, frame_anotado = detector.detectar_e_desenhar(frame)
            cv2.imshow("Catch Duo - câmera", frame_anotado)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q"):
                self._erro = "Janela da câmera fechada pelo usuário."
                break
            with self._lock:
                self._ultimo = QuadroVisao(pessoas, frame_anotado, agora_ms())
        cap.release(); detector.fechar(); cv2.destroyWindow("Catch Duo - câmera")

    def ultimo(self) -> QuadroVisao | None:
        with self._lock: return self._ultimo

    def parar(self): self._rodando = False
```

### `pose_detector.py`
Encapsula o MediaPipe Solutions. Retorna landmarks corporais completos para desenhar as conexões da cabeça aos pés e deriva de quadris o centro X usado para controlar o jogador. No modo de dois jogadores, cada região lateral usa uma instância independente de `Pose`.

```python
class PoseDetector:
    def __init__(self, num_jogadores=2):
        self.poses = [mp.solutions.pose.Pose(...) for _ in range(num_jogadores)]

    def detectar_e_desenhar(self, frame_bgr):
        altura_frame, largura_frame = frame_bgr.shape[:2]
        regioes = dividir_em_regioes(frame_bgr, len(self.poses))
        pessoas = []
        frame_anotado = frame_bgr.copy()
        for pose, (regiao, deslocamento_x, largura_regiao) in zip(self.poses, regioes):
            rgb = cv2.cvtColor(regiao, cv2.COLOR_BGR2RGB)
            resultado = pose.process(rgb)
            if resultado.pose_landmarks:
                # Converte X da região para o frame inteiro; Y permanece normalizado.
                landmarks_frame = converter_landmarks_para_frame(
                    resultado.pose_landmarks.landmark,
                    deslocamento_x,
                    largura_regiao,
                    largura_frame,
                )
                mp_drawing.draw_landmarks(
                    frame_anotado,
                    criar_landmark_list(landmarks_frame),
                    mp_pose.POSE_CONNECTIONS,
                )
                pessoas.append(extrair_pessoa(landmarks_frame, frame_anotado))
        return pessoas, frame_anotado

def extrair_pessoa(landmarks, frame_bgr) -> PessoaDetectada | None:
    # MediaPipe fornece a pose completa; quadris são a referência estável para mover em X.
    quadril_esq, quadril_dir = landmarks[23], landmarks[24]
    if min(quadril_esq.visibility, quadril_dir.visibility) < CONFIANCA_POSE:
        return None
    cx = (quadril_esq.x + quadril_dir.x) / 2
    cy = (quadril_esq.y + quadril_dir.y) / 2
    tamanho = abs(landmarks[11].x - landmarks[12].x)
    cor = cor_media_da_regiao_corporal(frame_bgr, cx, cy, tamanho)
    return PessoaDetectada(cx, cy, tamanho, cor)
```

### `mapeamento.py`
Converte posição da câmera em posição do jogo e suaviza o tremor.

```python
def cx_para_jogo(cx, largura_jogo=LARGURA, meia_largura=LARGURA_JOGADOR/2):
    # Só uma faixa central da câmera é usada (os jogadores não precisam encostar nas bordas)
    t = clamp((cx - ZONA_CAMERA_MIN) / (ZONA_CAMERA_MAX - ZONA_CAMERA_MIN), 0, 1)
    return meia_largura + t * (largura_jogo - 2 * meia_largura)

class SuavizadorEMA:
    """Média móvel exponencial: valor = alpha*novo + (1-alpha)*anterior."""
    def __init__(self, alpha=SUAVIZACAO_ALPHA): ...
    def aplicar(self, valor) -> float: ...
```

### `player_tracker.py` (a parte mais importante)
Lógica **pura** (sem OpenCV, sem MediaPipe, sem pygame), por isso fácil de testar com dados falsos.

Responsabilidades:
1. Dizer quem é P1 e quem é P2.
2. Manter a identidade de cada um ao longo do jogo.
3. Detectar **cruzamento** e **falta de jogador**.
4. Dizer quando os dois estão **na posição inicial** (para começar ou retomar).

```python
class PlayerTracker:
    def __init__(self):
        self.p1 = None            # último PessoaDetectada de P1
        self.p2 = None
        self.travado = False      # identidades já foram definidas?
        self.frames_sem_gente = 0
        self.inicio_estabilidade = None

    def atualizar(self, pessoas: list[PessoaDetectada], agora: float) -> EstadoJogadores:
        pessoas = [p for p in pessoas if p]
        pessoas = as_duas_maiores(pessoas)               # ignora gente ao fundo (menor "tamanho")

        # 1) Menos de 2 pessoas
        if len(pessoas) < 2:
            self.frames_sem_gente += 1
            if self.frames_sem_gente > TOLERANCIA_FRAMES:    # tolera piscadas de ~0,3 s
                return self._estado(FALTA_JOGADOR)
            return self._estado_anterior()                   # segura a última posição conhecida
        self.frames_sem_gente = 0

        # 2) Ainda não travou identidades (início / reposicionando)
        if not self.travado:
            return self._tentar_posicao_inicial(pessoas, agora)

        # 3) Rastreando: associa cada pessoa ao P1/P2 anterior
        a, b = pessoas
        custo_direto  = distancia(a, self.p1) + distancia(b, self.p2)
        custo_trocado = distancia(a, self.p2) + distancia(b, self.p1)
        novo_p1, novo_p2 = (a, b) if custo_direto <= custo_trocado else (b, a)
        # distancia() combina: diferença de cx, de cy, de tamanho e de cor da camisa

        self.p1, self.p2 = novo_p1, novo_p2

        # 4) Cruzamento: P1 passou para a direita de P2
        if self.p1.cx > self.p2.cx + MARGEM_CRUZAMENTO:
            self.travado = False                       # perde a identidade; exige reposicionar
            return self._estado(CRUZARAM)

        return self._estado(OK)

    def _tentar_posicao_inicial(self, pessoas, agora):
        esq, dir_ = sorted(pessoas, key=lambda p: p.cx)      # aqui ordenar por x é o critério
        na_posicao = (esq.cx  < 0.5 - MARGEM_CENTRAL and
                      dir_.cx > 0.5 + MARGEM_CENTRAL)
        if not na_posicao:
            self.inicio_estabilidade = None
            return self._estado(REPOSICIONANDO)
        if self.inicio_estabilidade is None:
            self.inicio_estabilidade = agora
        if agora - self.inicio_estabilidade >= TEMPO_ESTABILIDADE:    # ex.: 1 segundo parados
            self.p1, self.p2 = esq, dir_       # RE-SINCRONIZA: quem está à esquerda é P1
            self.travado = True
            self.inicio_estabilidade = None
            return self._estado(OK, prontos=True)
        return self._estado(REPOSICIONANDO)
```

Por que ordenar por `x` só na posição inicial e não o tempo todo? Porque, se ordenássemos por `x` em todo frame, o jogador "da esquerda" seria sempre quem está mais à esquerda — e nunca perceberíamos que eles trocaram de lado. Por isso a identidade é **travada** na posição inicial e seguida por proximidade.

Como o jogo **volta a funcionar**: depois de `CRUZARAM`/`FALTA_JOGADOR`, o tracker volta a `travado = False`. Quando os dois estiverem de novo cada um de um lado da linha central e parados por 1 s, ele **re-sincroniza** (esquerda = P1, direita = P2) e devolve `prontos=True`. Essa re-sincronização não depende de a identidade antiga estar correta.

---

## 6. Camada de entrada (`src/controllers/input/`)

### `input_source.py`
Interface única para teclado e câmera.

```python
@dataclass
class EntradaJogadores:
    dir_p1: int | None        # -1, 0, +1 (teclado)   | None se usar alvo
    dir_p2: int | None
    alvo_p1: float | None     # posição-alvo em pixels (câmera) | None se usar direção
    alvo_p2: float | None
    status: StatusJogadores   # OK / FALTA_JOGADOR / CRUZARAM / REPOSICIONANDO
    prontos: bool             # posição inicial confirmada
    debug: object | None      # QuadroVisao + EstadoJogadores, para diagnóstico; não desenhar no GameView

class InputSource(ABC):
    def ler(self) -> EntradaJogadores: ...
    def tratar_evento(self, evento, model): ...    # teclas gerais (ESPAÇO, P, R, ESC)
    def fechar(self): ...
```

### `keyboard_input.py`
É o antigo `input_controller.py`, adaptado à interface. Sempre retorna `status=OK` e `prontos=True`.

### `camera_input.py`

```python
class CameraInput(InputSource):
    def __init__(self):
        self.worker = CameraWorker(); self.worker.start()
        self.tracker = PlayerTracker()
        self.suav_p1, self.suav_p2 = SuavizadorEMA(), SuavizadorEMA()

    def ler(self):
        quadro = self.worker.ultimo()
        if quadro is None:                                # câmera ainda aquecendo
            return EntradaJogadores(status=REPOSICIONANDO, prontos=False, ...)

        estado = self.tracker.atualizar(quadro.pessoas, agora())

        alvo1 = alvo2 = None
        if estado.p1_cx is not None and estado.p2_cx is not None:
            alvo1 = self.suav_p1.aplicar(cx_para_jogo(estado.p1_cx))
            alvo2 = self.suav_p2.aplicar(cx_para_jogo(estado.p2_cx))

        return EntradaJogadores(None, None, alvo1, alvo2, estado.status, estado.prontos,
                                debug=(quadro, estado))

    def tratar_evento(self, evento, model): ...   # mesmas teclas gerais do teclado
    def fechar(self): self.worker.parar()
```

---

## 7. Mudanças no Model

### `player.py`
```python
class Player:
    ...
    self.direcao = 0          # continua (teclado)
    self.alvo_x = None        # NOVO (câmera): se não for None, o jogador "persegue" esse x

    def deslocamento(self, dt, velocidade):
        if self.alvo_x is not None:
            passo = clamp(self.alvo_x - self.x, -velocidade*dt, velocidade*dt)
            self.direcao = sinal(passo)          # mantém direcao coerente para as regras de bloqueio
            return passo
        return self.direcao * velocidade * dt
```

### `game_model.py`
- Novos estados: `"CALIBRANDO"` e `"PAUSADO_POSICAO"`.
- Novos métodos:

```python
def iniciar_calibracao(self):      self.estado = "CALIBRANDO"
def pausar_por_posicao(self):
    if self.estado == "JOGANDO": self.estado = "PAUSADO_POSICAO"
def retomar_por_posicao(self):
    if self.estado == "PAUSADO_POSICAO": self.estado = "JOGANDO"
```

- `mover_jogadores` passa a usar `deslocamento()`; **as regras de parede e de bloqueio entre jogadores não mudam**:

```python
def mover_jogadores(self, dt):
    v = VELOCIDADE_JOGADOR_CAMERA if self.usa_camera else VELOCIDADE_JOGADOR
    novo_p1 = self.p1.x + self.p1.deslocamento(dt, v)
    novo_p2 = self.p2.x + self.p2.deslocamento(dt, v)
    # ... restante igual ao da v1: paredes, distância mínima, "um empurrando o outro = ninguém anda"
```

Com a câmera, isso mantém a cooperação do jogo original: se o jogador da direita quiser pegar algo no canto esquerdo, o corpo dele vai para a esquerda, mas o triângulo só chega lá se o jogador da esquerda também tiver ido para o canto.

> `VELOCIDADE_JOGADOR_CAMERA` deve ser maior que a do teclado (ex.: 800 px/s), senão o triângulo fica "atrasado" em relação ao corpo.

---

## 8. Mudanças na View

### Janela OpenCV independente
O `CameraInput.ler`, chamado no loop principal, exibe o frame anotado em `Catch Duo - câmera`, fora da janela Pygame. Desenhar o esqueleto completo e marcadores de P1/P2 nessa imagem. Usar `cv2.waitKey(1)` para manter a janela responsiva; ao pressionar `Q` ou fechar a janela, sinalizar encerramento ao `CameraInput` e liberar os recursos da thread.

### `screens_view.py` (alterado)
- `desenhar_calibracao(debug)`: "Fiquem um de cada lado da linha central" + barra de progresso do 1 s de estabilidade. A imagem ao vivo fica na janela OpenCV.
- `desenhar_reposicionar(motivo)`: "Jogo pausado – voltem às posições iniciais". Mostra o motivo: "Vocês trocaram de lado" ou "Não consigo ver os dois jogadores".

### `game_view.py` (alterado)
`render(model)` — desenha somente a janela do jogo; não converte nem desenha frames da webcam.

---

## 9. Mudanças no Controller

### `game_controller.py`

```python
class GameController:
    def __init__(self, tela, input_source):
        self.model = GameModel()
        self.view = GameView(tela)
        self.input = input_source            # KeyboardInput ou CameraInput
        ...

    def run(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000
            for evento in pygame.event.get():
                if self.input.tratar_evento(evento, self.model) is False:
                    self.rodando = False

            entrada = self.input.ler()
            self._aplicar_entrada(entrada)

            self.model.update(dt)
            self.view.render(self.model, entrada.debug)
        self.input.fechar()

    def _aplicar_entrada(self, e):
        m = self.model
        if m.estado == "CALIBRANDO":
            if e.prontos: m.iniciar()
        elif m.estado == "PAUSADO_POSICAO":
            if e.status == OK and e.prontos: m.retomar_por_posicao()
        elif m.estado == "JOGANDO":
            if e.status != OK:
                m.pausar_por_posicao(); return
            if e.alvo_p1 is not None:               # modo câmera
                m.p1.alvo_x, m.p2.alvo_x = e.alvo_p1, e.alvo_p2
            else:                                    # modo teclado
                m.p1.direcao, m.p2.direcao = e.dir_p1, e.dir_p2
```

> Importante: ao entrar em `PAUSADO_POSICAO`, os triângulos simplesmente ficam onde estão. Ao retomar, o `alvo_x` volta a seguir os corpos e os triângulos "deslizam" até a nova posição, limitados pela velocidade máxima.

### `main.py`

```python
def main():
    args = ler_argumentos()                  # --input camera|teclado   (padrão: camera)
    pygame.init(); tela = pygame.display.set_mode((LARGURA, ALTURA))

    if args.input == "camera":
        try:
            fonte = CameraInput()
        except CameraIndisponivelError:
            print("Câmera não encontrada, usando teclado.")
            fonte = KeyboardInput()
    else:
        fonte = KeyboardInput()

    GameController(tela, fonte).run()
```

---

## 10. `config.py` – constantes novas

```python
# Entrada
MODO_ENTRADA_PADRAO = "camera"       # "camera" | "teclado"

# Câmera
CAMERA_INDICE = 0
CAMERA_LARGURA, CAMERA_ALTURA = 640, 480
POSE_COMPLEXITY = 1                # prioriza corpo inteiro; reduzir para 0 se o FPS cair
CONFIANCA_POSE = 0.5
CAMERA_JANELA_NOME = "Catch Duo - câmera"

# Mapeamento câmera -> jogo
ZONA_CAMERA_MIN, ZONA_CAMERA_MAX = 0.10, 0.90   # faixa horizontal da câmera que vale
SUAVIZACAO_ALPHA = 0.35                         # 0 = muito suave/lento, 1 = sem suavização
VELOCIDADE_JOGADOR_CAMERA = 800

# Posição inicial / pausa por posição
MARGEM_CENTRAL = 0.05           # cada um precisa estar ao menos 5% afastado da linha central
MARGEM_CRUZAMENTO = 0.02        # histerese para não pausar por pequenos encostos
TEMPO_ESTABILIDADE = 1.0        # segundos na posição inicial para (re)começar
TOLERANCIA_FRAMES = 10          # frames sem ver 2 pessoas antes de considerar "faltando"

# Pesos da distância usada para seguir cada jogador
PESO_POSICAO, PESO_TAMANHO, PESO_COR = 1.0, 0.5, 0.5
```

---

## 11. Riscos e como reduzi-los

| Risco | Mitigação |
|---|---|
| **Troca de identidade** quando os jogadores se cruzam e um cobre o outro. | O tracker combina posição, tamanho e **cor da camisa**. Se a detecção falhar durante o cruzamento, cai em `FALTA_JOGADOR` e o jogo pausa do mesmo jeito. Recomendar camisas de cores diferentes. |
| **Gente ao fundo** sendo detectada. | Validar a confiança e a visibilidade do corpo inteiro; rejeitar poses incompletas e manter cada jogador restrito à sua região lateral. |
| **Tremor** na posição. | `SuavizadorEMA` + usar o ponto médio dos quadris, sem seguir mãos e pés para controlar X. |
| **Atraso (lag)**. | Thread separada, modelo `lite`, resolução 640×480. Se ainda pesar, rodar a detecção a cada 2 frames. |
| **Pouca luz / contra a luz**. | Câmera na altura do peito, luz de frente, fundo simples. O `scripts/testar_camera.py` ajuda a conferir antes. |
| **Jogadores fora do enquadramento** (cabeça ou pés cortados). | Ajustar distância e altura da câmera para manter o corpo inteiro visível; exibir estado de pose incompleta e não atualizar o alvo até os quadris e pontos corporais de referência estarem visíveis. |
| **Câmera ausente**. | `main.py` cai para o modo teclado. |

---

## 12. Testes

| Arquivo | O que verifica |
|---|---|
| `test_player_tracker.py` | (a) Duas pessoas, uma em cada metade, por 1 s → `prontos=True` e P1 = esquerda. (b) Uma pessoa some por mais que a tolerância → `FALTA_JOGADOR`. (c) P1 passa para a direita de P2 → `CRUZARAM`. (d) Depois do cruzamento, só volta a `OK` após ficarem 1 s cada um de um lado. (e) Piscada curta (poucos frames sem detecção) **não** pausa. (f) Pessoa pequena ao fundo é ignorada. |
| `test_mapeamento.py` | `cx_para_jogo` nos extremos e no centro; EMA converge e reduz variação. |
| `test_model_alvo.py` | Com `alvo_x`, o jogador respeita a velocidade máxima; continua sem atravessar o outro; um indo para cada lado em direção ao outro não sai do lugar; estados `PAUSADO_POSICAO` congelam itens e tempo. |
| `test_keyboard_input.py` | `KeyboardInput` devolve `status=OK` e `prontos=True`. |

Como o `PlayerTracker` e o `mapeamento` não dependem de câmera, esses testes usam listas de `PessoaDetectada` criadas à mão.

---

## 13. Ordem sugerida de desenvolvimento

1. **Câmera sozinha** – `scripts/testar_camera.py`: abrir a webcam com OpenCV, espelhar e mostrar.
2. **Uma pessoa** – usar `mp.solutions.pose.Pose`, desenhar o esqueleto da cabeça aos pés e extrair o centro dos quadris para o controle lateral.
3. **Duas pessoas** – dividir a imagem em regiões, usar uma instância `Pose` para cada lado e desenhar os dois esqueletos no frame completo.
4. **Janela e thread** – o `CameraWorker` captura/processa; `CameraInput.ler` exibe a webcam em janela OpenCV separada no loop principal e mantém a janela Pygame fluida.
5. **Tracker puro** – escrever `PlayerTracker` + `test_player_tracker.py` com dados falsos, até todos os cenários passarem.
6. **Mapeamento + alvo_x** – `mapeamento.py`, `Player.deslocamento`, ajuste do `mover_jogadores` e `test_model_alvo.py`.
7. **Interface de entrada** – criar `InputSource`, mover o teclado para `KeyboardInput` e garantir que o jogo v1 continua igual.
8. **CameraInput + estados** – `CameraInput`, estados `CALIBRANDO`/`PAUSADO_POSICAO` e o `_aplicar_entrada` do controller.
9. **Janelas e telas** – remover `CameraPreviewView`, deixar telas de calibração/reinício na janela Pygame e imagem anotada na janela OpenCV.
10. **Ajuste fino** – `ZONA_CAMERA_*`, `SUAVIZACAO_ALPHA`, complexidade, visibilidade mínima e velocidade; validar corpos inteiros e os dois jogadores.

---

## 14. Ideias extras (opcionais)

- Botão/tecla para **recalibrar** a qualquer momento (`C`).
- Contagem regressiva "3, 2, 1" ao retomar depois de uma pausa por posição.
- Controle alternativo por **inclinação do corpo** (direção) em vez de posição absoluta, caso o espaço físico seja pequeno.
- Escolher automaticamente a câmera disponível (`CAMERA_INDICE`) com uma tela de seleção.
- Salvar um `config_usuario.json` com a calibração (zona útil da câmera) para a próxima sessão.
