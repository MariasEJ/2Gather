# Guia de configuração do Catch Duo

As opções principais ficam em `src/config.py`.

## Tela e aparência

| O que alterar | Arquivo | Variável |
|---|---|---|
| Largura da janela | `src/config.py` | `LARGURA` |
| Altura da janela | `src/config.py` | `ALTURA` |
| Limite de quadros por segundo | `src/config.py` | `FPS` |
| Título da janela | `src/config.py` | `TITULO` |
| Cor de fundo | `src/config.py` | `COR_FUNDO` |
| Cor dos painéis do menu, pausa e fim | `src/config.py` | `COR_PAINEL` |
| Cor do texto principal | `src/config.py` | `COR_TEXTO` |
| Cor de textos secundários | `src/config.py` | `COR_TEXTO_SUAVE` |
| Cor do jogador P1 | `src/config.py` | `COR_P1` |
| Cor do jogador P2 | `src/config.py` | `COR_P2` |
| Cor das bolinhas de vida preenchidas | `src/config.py` | `COR_VIDA` |
| Cor das bolinhas de vida perdidas | `src/config.py` | `COR_VIDA_VAZIA` |
| Cores possíveis dos itens | `src/config.py` | `CORES_ITENS` |
| Posição, raio e espaçamento das vidas | `src/views/hud_view.py` | `raio`, `espacamento`, `primeiro_centro_x`, `centro_y` |
| Tamanho da fonte da pontuação | `src/views/hud_view.py` | `HudView.__init__`, `pygame.font.Font(None, 46)` |
| Formato, tamanho e posição dos botões do menu | `src/views/screens_view.py` | `botao_iniciar`, `botao_regras`, `botao_voltar` |
| Cores dos botões | `src/views/screens_view.py` | método `_botao` |
| Tamanho das fontes das telas | `src/views/screens_view.py` | `fonte_titulo`, `fonte`, `fonte_pequena` |
| Aparência do cenário e linha do chão | `src/views/game_view.py` | método `_desenhar_cenario` |

As cores usam o formato RGB: `(vermelho, verde, azul)`, com cada canal entre `0` e `255`.

## Modo de jogadores e entrada

| O que alterar | Arquivo | Variável ou função |
|---|---|---|
| Jogar com uma ou duas pessoas | `main.py` | `NUM_JOGADORES = 1` ou `NUM_JOGADORES = 2` |
| Usar webcam ou teclado | `main.py` | `USAR_CAMERA = True` ou `USAR_CAMERA = False` |
| Número de jogadores detectados | `src/controllers/input/camera_input.py` | `CameraInput(num_jogadores)` |
| Formatos de item que aparecem em cada modo | `src/models/item_spawner.py` | método `ItemSpawner.update` |
| Índice da webcam | `src/config.py` | `CAMERA_INDICE` |
| Resolução de captura | `src/config.py` | `CAMERA_LARGURA`, `CAMERA_ALTURA` |
| Limites laterais usados para mapear o corpo | `src/config.py` | `ZONA_CAMERA_MIN`, `ZONA_CAMERA_MAX` |
| Suavização do movimento (`1` responde imediatamente) | `src/config.py` | `SUAVIZACAO_ALPHA` |
| Velocidade máxima do jogador na câmera | `src/config.py` | `VELOCIDADE_JOGADOR_CAMERA` |
| Visibilidade mínima dos dois quadris para controlar | `src/config.py` | `CONFIANCA_QUADRIS` |
| Confiança de detecção/rastreamento do MediaPipe | `src/config.py` | `CONFIANCA_POSE` |
| Tempo de detecção para calibrar/retomar | `src/config.py` | `TEMPO_ESTABILIDADE` |
| Margem de cada lado da linha central | `src/config.py` | `MARGEM_CENTRAL` |
| Margem para declarar cruzamento | `src/config.py` | `MARGEM_CRUZAMENTO` |
| Quadros sem detecção tolerados | `src/config.py` | `TOLERANCIA_FRAMES` |
| Leituras falhas consecutivas antes do fallback | `src/config.py` | `CAMERA_MAX_LEITURAS_FALHAS` |
| Prazo para receber o primeiro quadro (segundos) | `src/config.py` | `CAMERA_TIMEOUT_INICIAL` |
| Idade máxima do quadro antes do fallback (segundos) | `src/config.py` | `CAMERA_TIMEOUT_QUADRO` |
| Intervalo dos resumos de diagnóstico (segundos) | `src/config.py` | `INTERVALO_LOG_CAMERA` |
| Peso de posição, tamanho e cor ao manter identidade | `src/config.py` | `PESO_POSICAO`, `PESO_TAMANHO`, `PESO_COR` |
| Complexidade da detecção corporal (aumente para priorizar corpo inteiro) | `src/config.py` | `POSE_COMPLEXITY` |
| Confiança mínima de pose e visibilidade do corpo completo | `src/config.py` | `CONFIANCA_POSE`, `CONFIANCA_CORPO_COMPLETO` |
| Título da janela independente da webcam | `src/config.py` | `CAMERA_JANELA_NOME` |

No modo de um jogador, P1 é o único personagem e o gerador cria apenas círculos. No modo de dois jogadores, P1 fica à esquerda na calibração e pega círculos; P2 fica à direita e pega quadrados.

É possível sobrescrever os padrões de `main.py` com `--input camera|teclado`
e `--jogadores 1|2`. Logs são configurados em `src/logging_config.py`:
`--log-level DEBUG` detalha cada quadro, e `--log-file catch-duo.log` grava a
sessão além de mostrar no terminal. Em INFO, os resumos seguem
`INTERVALO_LOG_CAMERA`, e transições/erros aparecem imediatamente.

Ausência de pose com quadros novos exige reposicionamento. Falha de abertura,
exceção, fechamento da janela ou timeout de quadros ativa o teclado. A calibração
aceita os dois quadris visíveis dentro da imagem; cabeça e pés não bloqueiam o
início. Pequenas falhas de detecção respeitam `TOLERANCIA_FRAMES`.

## Arquivos da câmera

| Função | Arquivo | O que ajustar |
|---|---|---|
| Capturar e espelhar quadros em segundo plano | `src/vision/camera_worker.py` | `CameraWorker.run` |
| Configurar a detecção MediaPipe Solutions | `src/vision/pose_detector.py` | `PoseDetector._criar_pose` |
| Desenhar a pose completa e extrair posição dos quadris | `src/vision/pose_detector.py` | `detectar_e_desenhar`, `_extrair_pessoa` |
| Atribuir identidade, detectar cruzamento e ausência | `src/vision/player_tracker.py` | `PlayerTracker.atualizar`, `_associar_dupla`, `_tentar_calibracao` |
| Suavizar e mapear posição da câmera para pixels | `src/vision/mapeamento.py` | `cx_para_jogo`, `SuavizadorEMA.aplicar` |
| Traduzir resultados da câmera em alvos dos jogadores | `src/controllers/input/camera_input.py` | `CameraInput.ler` |
| Atualizar e fechar a janela OpenCV da câmera | `src/controllers/input/camera_input.py` | `_atualizar_janela`, `_destruir_janela` |
| Exibir instruções de calibração e reposicionamento | `src/views/screens_view.py` | `desenhar_calibracao`, `desenhar_reposicionar` |
| Aplicar entrada e transições de estado | `src/controllers/game_controller.py` | `_aplicar_entrada` |

O MediaPipe Solutions não precisa de arquivo de modelo separado. Com dois jogadores, `PoseDetector.detectar_e_desenhar` divide a imagem ao meio e processa cada região com uma instância independente. A janela da câmera é separada da janela Pygame e mostra o esqueleto completo. O controle lateral usa o ponto médio dos quadris; a detecção dos quadris é suficiente para calibrar e jogar, enquanto enquadrar o corpo inteiro ajuda o MediaPipe a desenhar a pose. A calibração aguarda cerca de um segundo de detecção válida sem exigir que a pessoa fique imóvel. Para conferir o enquadramento sem iniciar a partida, rode `python -m scripts.testar_camera` e pressione `Q` para sair.

## Como estender uma função

1. **Entrada:** implemente `ler()` e `fechar()` em uma classe baseada em `InputSource`, retornando `EntradaJogadores` em `src/controllers/input/input_source.py`.
2. **Visão:** coloque a detecção e o rastreamento em `src/vision/`; mantenha esses módulos sem imports de Pygame. Use `PessoaDetectada` e `EstadoJogadores` para passar dados.
3. **Regras:** altere estado e comportamento em `src/models/`. A View deve apenas desenhar o resultado.
4. **Interface:** altere as telas em `src/views/`. Para novos estados, ligue a transição no Model, o comando no Controller e a apresentação na View.
5. **Seleção de jogadores:** `NUM_JOGADORES` em `main.py` é passado para a fonte de entrada e para `GameModel`; preserve essa propagação ao criar outros modos.

As bibliotecas estão fixadas em `requirements.txt`. A detecção usa `mediapipe.solutions.pose.Pose.process`, sem Tasks API, sem serviço externo e sem baixar um arquivo de modelo. O pacote OpenCV contrib fornece o módulo `cv2` usado pelo projeto e satisfaz a dependência do MediaPipe. A versão MediaPipe fixada publica wheels até Python 3.12; use Python 3.12 ou anterior para instalar as dependências da câmera.

## Jogadores e itens

| O que alterar | Arquivo | Variável |
|---|---|---|
| Largura dos triângulos | `src/config.py` | `LARGURA_JOGADOR` |
| Altura dos triângulos | `src/config.py` | `ALTURA_JOGADOR` |
| Velocidade horizontal dos jogadores | `src/config.py` | `VELOCIDADE_JOGADOR` |
| Tamanho dos círculos e quadrados que caem | `src/config.py` | `TAMANHO_ITEM` |
| Velocidade inicial de queda | `src/config.py` | `VELOCIDADE_QUEDA_INICIAL` |
| Limite máximo da velocidade de queda | `src/config.py` | `VELOCIDADE_QUEDA_MAXIMA` |
| Tipo de item que cada jogador captura | `src/models/game_model.py` | `GameModel.reset`, `tipo_alvo` de `p1` e `p2` |
| Forma visual do jogador | `src/views/game_view.py` | método `desenhar_jogador` |
| Forma visual dos itens | `src/views/game_view.py` | método `desenhar_item` |

## Pontuação, vidas e dificuldade

| O que alterar | Arquivo | Variável |
|---|---|---|
| Pontos por captura correta | `src/config.py` | `PONTOS_ACERTO` |
| Pontos por captura errada | `src/config.py` | `PONTOS_ERRO` |
| Limite mínimo da pontuação (`None` permite pontos negativos) | `src/config.py` | `PONTUACAO_MINIMA` |
| Quantidade de bolinhas de vida/perdas permitidas | `src/config.py` | `MAX_ITENS_PERDIDOS` |
| Pontuação que encerra a partida por erros | `src/config.py` | `PONTUACAO_LIMITE_INFERIOR` |
| Intervalo inicial entre itens | `src/config.py` | `INTERVALO_SPAWN_INICIAL` |
| Menor intervalo permitido entre itens | `src/config.py` | `INTERVALO_SPAWN_MINIMO` |
| Pontos líquidos para avançar um nível de dificuldade | `src/config.py` | `PONTOS_POR_NIVEL_DIFICULDADE` |
| Aumento de velocidade por nível | `src/config.py` | `AUMENTO_VELOCIDADE_POR_NIVEL` |
| Redução do intervalo de spawn por nível | `src/config.py` | `REDUCAO_SPAWN_POR_NIVEL` |
| Regra de cálculo da velocidade e do intervalo | `src/models/item_spawner.py` | método `ItemSpawner.update` |

`MAX_ITENS_PERDIDOS` define a quantidade de vidas. Cada item que chega ao chão remove uma bolinha inteira; o padrão é `3` vidas.

O nível de dificuldade é calculado pela pontuação compartilhada dividida por `PONTOS_POR_NIVEL_DIFICULDADE`. Cada nível reduz o intervalo entre itens e aumenta a velocidade de queda; o intervalo e a velocidade respeitam os limites mínimo e máximo configurados.

## Regras e controles

| O que alterar | Arquivo | Variável ou trecho |
|---|---|---|
| Teclas de movimento no modo teclado | `src/controllers/input/keyboard_input.py` | método `KeyboardInput.ler` |
| Teclas de iniciar, pausar e reiniciar | `src/controllers/input_controller.py` | método `tratar_evento` |
| Textos da tela de regras | `src/views/screens_view.py` | método `desenhar_regras` |
| Textos do menu inicial | `src/views/screens_view.py` | método `desenhar_menu` |
| Condições de fim de jogo | `src/models/game_model.py` | método `update`, `MAX_ITENS_PERDIDOS` e `PONTUACAO_LIMITE_INFERIOR` |
