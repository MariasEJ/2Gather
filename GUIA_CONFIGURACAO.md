# Guia de configuração do 2Gather

As regras de tela e entrada estão em `src/config.py`; os dados de cada lixeira ficam em sua própria classe dentro de `src/models/lixeiras/`, por exemplo `src/models/lixeiras/vidro.py`.

## Tela e movimento

| O que ajustar | Arquivo | Parâmetros |
|---|---|---|
| Janela, taxa de quadros e título | `src/config.py` | `LARGURA`, `ALTURA`, `FPS`, `TITULO` |
| Altura do chão e faixa preta | `src/config.py` | `CHAO_Y`, `ALTURA_FAIXA_INFERIOR` |
| Tamanho e velocidade das lixeiras | `src/config.py` | `LARGURA_JOGADOR`, `ALTURA_JOGADOR`, `VELOCIDADE_JOGADOR` |
| Suavização, velocidade e regiões da câmera | `src/config.py` | `SUAVIZACAO_ALPHA`, `VELOCIDADE_JOGADOR_CAMERA`, `ZONA_CAMERA_MIN`, `ZONA_CAMERA_MAX`, `MARGEM_CENTRAL` |
| Posição inicial e bloqueio entre lixeiras | `src/models/game_model.py` | `mover_jogadores` |
| Quatro faixas invisíveis | `src/config.py`, `src/models/particoes.py` | `NUM_PARTICOES`, `particao_x` |
| Cenário, faixa e imagens | `src/views/game_view.py` | `_desenhar_cenario`, `desenhar_item` |

`ALTURA_FAIXA_INFERIOR = 120` define a faixa preta vazia. O chão é calculado por `CHAO_Y = ALTURA - ALTURA_FAIXA_INFERIOR`, atualmente y=480. As lixeiras têm 112 × 112 pixels e ficam em y=368; só o centro horizontal varia. P1 começa na faixa 2 e alcança 1–3. P2 começa na faixa 3 e alcança 2–4. Cada faixa ocupa 200 pixels; as faixas 2 e 3 são compartilhadas. A distância mínima entre os centros é 112 pixels, sem cruzamento.

## Seleção de entrada e calibração

Edite `USAR_CAMERA` em `src/config.py`, salve e reinicie o programa. `True` cria uma entrada de câmera para duas pessoas; `False` cria a entrada de teclado sem importar ou inicializar a câmera. A variável é o único seletor do modo. Não há modo solo, argumento de quantidade de jogadores ou fallback automático.

| Ação | Câmera | Teclado |
|---|---|---|
| P1 move a lixeira | Movimento lateral na metade esquerda | A / D |
| P2 move a lixeira | Movimento lateral na metade direita | ← / → |
| Iniciar ou reiniciar | Agachamento simultâneo por 0,6 s | Espaço |
| Abrir informações, apenas no menu ou resultado | Pulo de qualquer jogador | X |
| Fechar informações | Novo pulo, ESC ou Voltar | X, ESC ou Voltar |

`TEMPO_ESTABILIDADE` define a duração mínima da calibração. `AMOSTRAS_CALIBRACAO` e `OSCILACAO_CALIBRACAO` exigem amostras recentes e quadris estáveis em pé. `LIMIAR_AGACHAMENTO = 0.05` segue a descida normalizada do quadril do HerPules. `CONFIANCA_QUADRIS` filtra landmarks pouco visíveis; `CONFIANCA_GESTOS` define a confiança mínima para gestos. `TEMPO_CONFIRMACAO_GESTO = 0.6` confirma o agachamento conjunto em quadros novos.

O pulo usa referências individuais de quadris e tornozelos, com `LIMIAR_PULO = 0.06` e `LIMIAR_PES_PULO = 0.04`. `VELOCIDADE_MIN_SUBIDA` é medida por segundo para funcionar com taxas diferentes de captura. `COOLDOWN_PULO = 0.5` e o retorno ao chão evitam múltiplos comandos no mesmo salto, inclusive quando a dupla pula quase ao mesmo tempo. Quadros repetidos ou separados por mais de `INTERVALO_MAX_AMOSTRAS_PULO` não produzem pulos. Se os pés só entrarem no enquadramento depois, fiquem em pé durante 30 novas amostras para calibrá-los. Braços em X não acionam mais o menu.

`TEMPO_RECUPERACAO_POSE = 0.5` permite recuperar uma perda breve sem repetir a calibração, desde que os jogadores sejam associados com segurança e retornem em pé aos seus lados. Durante a perda, os alvos ausentes ficam neutros; referências antigas nunca simulam um pulo.

A câmera processa duas regiões independentes. `src/vision/player_tracker.py` mantém as referências e associações P1/P2. Se perder os dois alvos ou não puder garantir suas identidades, neutraliza os controles e registra o estado no log e na janela da câmera; não pausa a partida e não troca as identidades. Se um único alvo ainda puder ser associado com segurança, apenas aquela lixeira continua recebendo movimento. Falha definitiva segue a mesma regra e não ativa o teclado. Fechar a janela principal libera os recursos.

Outros parâmetros da captura estão em `src/config.py`: `CAMERA_INDICE`, `CAMERA_LARGURA`, `CAMERA_ALTURA`, `CAMERA_MAX_LEITURAS_FALHAS`, `CAMERA_TIMEOUT_INICIAL`, `CAMERA_TIMEOUT_QUADRO` e `INTERVALO_LOG_CAMERA`. `scripts/testar_camera.py` ajuda a conferir o enquadramento dos quadris e a divisão da câmera.

### Desempenho da câmera

| Parâmetro | Padrão | Efeito |
|---|---|---|
| `POSE_COMPLEXITY` | `0` | Modelo Lite; `1` usa Full, com maior custo de inferência |
| `CAMERA_LARGURA`, `CAMERA_ALTURA` | `640`, `480` | Resolução solicitada ao driver |
| `CAMERA_DESENHAR_LANDMARKS` | `False` | Prévia recente sem esqueleto; `True` mostra o frame processado com landmarks |
| `SUAVIZACAO_ALPHA` | `0.7` | Maior peso para a posição recente; reduzir suaviza mais, mas acrescenta atraso |
| `CAMERA_MAX_IDADE_POSE` | `0.25` s | Neutraliza comandos cuja imagem ficou antiga; recupera ao receber uma pose recente |
| `INTERVALO_LOG_CAMERA` | `2.0` s | Intervalo dos logs de FPS de captura/inferência, duração e idade da pose |

A captura e a inferência têm threads separadas. O buffer do aplicativo guarda apenas o frame mais recente, descartando os intermediários quando a detecção não acompanha a câmera. `CAP_PROP_BUFFERSIZE = 1` também é solicitado, mas depende do driver. O modelo Lite pode exigir um download automático do MediaPipe no primeiro uso em um ambiente novo. A prévia mostra a duração da inferência e a idade da pose; os resultados medidos e suas limitações estão em [DESEMPENHO.md](DESEMPENHO.md).

## Classes de lixeiras e resíduos

Os arquivos `papel.py`, `plastico.py`, `vidro.py`, `metal.py` e `organico.py` em `src/models/lixeiras/` contêm as classes de cada lixeira. Cada classe define:

| Atributo | Conteúdo |
|---|---|
| `ID`, `NOME` | Identidade da categoria e nome usado na tela de regras |
| `IMAGEM` | Caminho da imagem da lixeira dentro do projeto |
| `ITENS` | Lista de resíduos da classe, com quantidade livre e pelo menos um item |

Cada `Residuo` em `ITENS` define `id`, `nome`, `imagem` e `tamanho`. Use uma nova subclasse para acrescentar uma categoria e associe a ela seus próprios resíduos. `LIXEIRAS` contém as cinco classes elegíveis ao sorteio; o sorteio escolhe duas classes distintas apenas depois da confirmação da dupla. `src/models/item_spawner.py` consulta diretamente as classes sorteadas, sem criar gerador individual por lixeira.

O tamanho pode ser um inteiro positivo ou `(largura, altura)`, em pixels. Por exemplo, em `metal.py`: `Residuo('metal_lata', 'Lata de conserva', 'imagens/lixo-lata2.png', tamanho=(48, 56))`. A imagem mantém a proporção dentro dessa área, que também é usada na captura. Os nomes e as listas de resíduos aparecem apenas nas regras.

Os tamanhos foram ampliados individualmente: PET de água usa 76 × 76 (imagem diagonal), PET de refrigerante 50 × 84, latinhas 38 × 48, garrafa de vidro 42 × 80 e esmalte 36 × 42. São proporções visuais para o jogo, não uma escala física exata.

## Classes de fundos e imagens

`src/models/fundos.py` contém `FundoSimples`, `FundoDecorado` e `FundoPraia`. Cada classe define `ID`, `NOME` e o caminho `IMAGEM`. O fundo é escolhido separadamente das lixeiras e só muda ao iniciar uma rodada confirmada.

| Elemento | Exemplo de caminho usado no código |
|---|---|
| Lixeira de vidro | `imagens/lixeira-reci-vidro.png` |
| Pote de vidro | `imagens/pote-vidro.png` |
| Fundo usado pela classe `FundoSimples` | `imagens/fundo1-simples.png` |

Para substituir uma lixeira, coloque o PNG na pasta `imagens/` e altere o atributo `IMAGEM` de sua classe. Por exemplo, em `LixeiraVidro`, use `IMAGEM = 'imagens/minha-lixeira-de-vidro.png'`. Para substituir um resíduo, altere a imagem e seu tamanho, como `Residuo('vidro_pote', 'Pote de vidro', 'imagens/meu-pote.png', tamanho=(32, 48))`. Para o fundo, altere `IMAGEM` na classe correspondente em `fundos.py`.

Os caminhos são relativos à raiz do projeto, independentemente da pasta usada para executar o jogo. Lixeiras são encaixadas em 112 × 112 com âncora inferior central; cada resíduo usa o tamanho informado na sua definição, com padrão 48 × 48. A captura usa essa área lógica, sem ler os pixels da imagem. Fundos preenchem os 800 × 480 pixels acima da faixa preta. Se um caminho estiver errado ou o arquivo faltar, o jogo informa qual imagem não encontrou.

## Pontos, vidas e dificuldade

| O que ajustar | Parâmetros em `src/config.py` |
|---|---|
| Pontos por captura correta/incorreta | `PONTOS_ACERTO`, `PONTOS_ERRO` |
| Piso opcional da pontuação | `PONTUACAO_MINIMA` |
| Vidas e fim por pontuação negativa | `MAX_ITENS_PERDIDOS`, `PONTUACAO_LIMITE_INFERIOR` |
| Velocidade e intervalo iniciais | `VELOCIDADE_QUEDA_INICIAL`, `INTERVALO_SPAWN_INICIAL` |
| Limites de velocidade e intervalo | `VELOCIDADE_QUEDA_MAXIMA`, `INTERVALO_SPAWN_MINIMO` |
| Progressão | `PONTOS_POR_NIVEL_DIFICULDADE`, `AUMENTO_VELOCIDADE_POR_NIVEL`, `REDUCAO_SPAWN_POR_NIVEL` |
| Duração 3, 2, 1 | `TEMPO_CONTAGEM` |

A rodada começa com 80 px/s e um resíduo a cada 4 s. A cada cinco pontos líquidos, os novos resíduos ganham 10 px/s e o intervalo cai 0,15 s, até 420 px/s e 0,32 s. Um primeiro resíduo aparece imediatamente ao terminar a contagem; a partir dele começa o intervalo normal. O item é perdido quando seu topo ultrapassa `CHAO_Y` (atualmente y=480), depois da verificação de captura daquele quadro.

## Arquitetura

| Responsabilidade | Arquivos |
|---|---|
| Categorias, movimento, captura e rodada | `src/models/player.py`, `falling_item.py`, `item_spawner.py`, `game_model.py`, `fundos.py` |
| Pose, identidades, quadris e gestos | `src/vision/pose_detector.py`, `player_tracker.py`, `gestos.py`, `tipos.py` |
| Seleção e confirmação das entradas | `src/controllers/input/__init__.py`, `camera_input.py`, `keyboard_input.py` |
| Telas e recursos visuais | `src/views/game_view.py`, `screens_view.py`, `hud_view.py`, `recursos_visuais.py` |

Dependências de câmera: Python 3.12 ou anterior e os pacotes fixados em `requirements.txt`. O modo teclado não precisa iniciar MediaPipe ou webcam.
