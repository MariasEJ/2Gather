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
| Teclas de movimento | `src/controllers/input_controller.py` | método `ler_direcoes` |
| Teclas de iniciar, pausar e reiniciar | `src/controllers/input_controller.py` | método `tratar_evento` |
| Textos da tela de regras | `src/views/screens_view.py` | método `desenhar_regras` |
| Textos do menu inicial | `src/views/screens_view.py` | método `desenhar_menu` |
| Condições de fim de jogo | `src/models/game_model.py` | método `update`, `MAX_ITENS_PERDIDOS` e `PONTUACAO_LIMITE_INFERIOR` |
