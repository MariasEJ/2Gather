# Catch Duo – Projeto (Python + Pygame, padrão MVC)

Jogo cooperativo para 2 jogadores no mesmo teclado. Itens (bolinhas e quadrados coloridos) caem do céu. Cada jogador controla um triângulo na parte de baixo da tela e só deve pegar o **seu tipo** de item.

---

## 1. Regras do jogo

| Tema | Regra |
|---|---|
| Jogadores | **P1 (esquerda)**: teclas `A` / `D` – pega **bolinhas**. **P2 (direita)**: setas `←` / `→` – pega **quadrados**. |
| Personagem | Triângulo (cores diferentes para cada jogador), fixo no chão da tela, só se move na horizontal. |
| Itens | Bolinhas e quadrados, cor aleatória (a cor não importa, só o formato). |
| Pontuação | **Única e compartilhada.** Item certo: `+1`. Item errado (ex.: P1 pega quadrado): `-1`. |
| Item perdido | Item que cai no chão sem ser pego: sem penalidade|
| Colisão entre jogadores | Um **não atravessa** o outro. P1 sempre fica à esquerda de P2. |
| Empurrão | Se um vai para a direita e o outro para a esquerda ao mesmo tempo, os dois ficam parados. |
| Fim de jogo | 3 ou mais itens perdidos|
| Dificuldade | A velocidade de queda e a frequência de spawn aumentam com o tempo. |

### Exemplo da mecânica de movimento

Se P2 (direita) precisa pegar um item no canto esquerdo, P1 tem que ir para o canto esquerdo também para liberar espaço. P2 só chega lá se P1 abrir caminho. Isso força os dois a conversarem e se coordenarem.

---

## 2. Visão geral do MVC neste projeto

```
        ┌────────────┐   lê teclado    ┌──────────────┐
Teclado │ Controller │ ──────────────► │    Model     │
  ────► │ (decide)   │  altera estado  │ (dados+regra)│
        └────────────┘                 └──────┬───────┘
                                              │ só leitura
                                       ┌──────▼───────┐
                                       │     View     │ ──► Tela
                                       │  (desenha)   │
                                       └──────────────┘
```

- **Model**: guarda o estado do jogo e as regras (posições, pontos, tempo, colisão). **Não importa `pygame` para desenhar nem lê teclado.** Dá para testar sem abrir janela.
- **View**: só desenha o que está no Model. **Nunca altera o Model.**
- **Controller**: lê o input, chama os métodos do Model a cada frame e manda a View desenhar. É o "maestro" do loop.

---

## 3. Estrutura de pastas

```
catch_duo/
├── main.py
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── falling_item.py
│   │   ├── item_spawner.py
│   │   └── game_model.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── game_view.py
│   │   ├── hud_view.py
│   │   └── screens_view.py
│   └── controllers/
│       ├── __init__.py
│       ├── input_controller.py
│       └── game_controller.py
└── tests/
    ├── test_player_movement.py
    ├── test_scoring.py
    └── test_spawner.py
```

---

## 4. O que cada arquivo faz

### Raiz

#### `main.py`
Ponto de entrada. Só inicializa o pygame, cria a janela e entrega para o controller.

```python
def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    controller = GameController(tela)
    controller.run()
    pygame.quit()

if __name__ == "__main__":
    main()
```

#### `requirements.txt`
```
pygame>=2.5
pytest
```

#### `README.md`
Como instalar (`pip install -r requirements.txt`), como rodar (`python main.py`), controles e regras.

---

### `src/config.py`
Todas as constantes do jogo em um lugar só (fácil de ajustar a dificuldade).

```python
# Tela
LARGURA, ALTURA, FPS = 800, 600, 60

# Jogadores
LARGURA_JOGADOR, ALTURA_JOGADOR = 60, 50
VELOCIDADE_JOGADOR = 350            # pixels por segundo
COR_P1, COR_P2 = (80, 160, 255), (255, 120, 80)

# Itens
TAMANHO_ITEM = 28
VELOCIDADE_QUEDA_INICIAL = 150
INTERVALO_SPAWN_INICIAL = 0.9       # segundos
CORES_ITENS = [(255,0,0),(0,200,0),(255,220,0),(180,0,255),(0,220,220)]

# Regras
PONTOS_ACERTO, PONTOS_ERRO = +1, -1
PONTUACAO_MINIMA = None             # ou 0 para não deixar ficar negativa
DURACAO_PARTIDA = 60                # segundos

# Controles (usar constantes do pygame)
TECLAS_P1 = {"esquerda": K_a, "direita": K_d}
TECLAS_P2 = {"esquerda": K_LEFT, "direita": K_RIGHT}
```

---

## 5. Models (`src/models/`)

### `player.py`
Representa um triângulo. Guarda posição e qual tipo de item ele deve pegar.

```python
class Player:
    def __init__(self, nome, x, cor, tipo_alvo):   # tipo_alvo: "circulo" ou "quadrado"
        self.nome = nome
        self.x = x                  # centro horizontal
        self.y = ALTURA - ALTURA_JOGADOR
        self.largura = LARGURA_JOGADOR
        self.cor = cor
        self.tipo_alvo = tipo_alvo
        self.direcao = 0            # -1 esquerda, 0 parado, +1 direita (definida pelo controller)

    def retangulo(self):
        """Retorna (x, y, w, h) da caixa de colisão (usada para pegar itens)."""
```

### `falling_item.py`
Um item que cai.

```python
class FallingItem:
    def __init__(self, x, tipo, cor, velocidade):
        self.x, self.y = x, -TAMANHO_ITEM
        self.tipo = tipo            # "circulo" ou "quadrado"
        self.cor = cor
        self.velocidade = velocidade
        self.ativo = True

    def update(self, dt):
        self.y += self.velocidade * dt

    def retangulo(self): ...
    def saiu_da_tela(self): return self.y > ALTURA
```

### `item_spawner.py`
Decide **quando** e **o que** criar. Usa `random` e um cronômetro (sem pygame).

```python
class ItemSpawner:
    def __init__(self):
        self.timer = 0
        self.intervalo = INTERVALO_SPAWN_INICIAL
        self.velocidade_queda = VELOCIDADE_QUEDA_INICIAL

    def update(self, dt, tempo_decorrido) -> list[FallingItem]:
        # 1. soma dt no timer
        # 2. se timer >= intervalo: zera timer e cria 1 item
        #      tipo  = random.choice(["circulo", "quadrado"])
        #      cor   = random.choice(CORES_ITENS)
        #      x     = random.randint(margem, LARGURA - margem)
        # 3. (opcional) aumenta dificuldade conforme tempo_decorrido
        # retorna lista de itens novos (vazia na maioria dos frames)
```

### `game_model.py`  (coração do jogo)
Reúne jogadores, itens, pontuação, tempo e **todas as regras**.

```python
class GameModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.p1 = Player("P1", x=LARGURA*0.25, cor=COR_P1, tipo_alvo="circulo")
        self.p2 = Player("P2", x=LARGURA*0.75, cor=COR_P2, tipo_alvo="quadrado")
        self.itens = []
        self.spawner = ItemSpawner()
        self.pontuacao = 0
        self.tempo_restante = DURACAO_PARTIDA
        self.estado = "MENU"        # MENU | JOGANDO | PAUSADO | FIM

    def update(self, dt):
        if self.estado != "JOGANDO": return
        self.mover_jogadores(dt)
        self.itens += self.spawner.update(dt, DURACAO_PARTIDA - self.tempo_restante)
        for item in self.itens: item.update(dt)
        self.verificar_capturas()
        self.remover_itens_inativos()
        self.tempo_restante -= dt
        if self.tempo_restante <= 0: self.estado = "FIM"
```

**Movimento + bloqueio entre jogadores** (o trecho mais importante):

```python
    def mover_jogadores(self, dt):
        meia = LARGURA_JOGADOR / 2
        novo_p1 = self.p1.x + self.p1.direcao * VELOCIDADE_JOGADOR * dt
        novo_p2 = self.p2.x + self.p2.direcao * VELOCIDADE_JOGADOR * dt

        # 1. limites das paredes
        novo_p1 = clamp(novo_p1, meia, LARGURA - meia)
        novo_p2 = clamp(novo_p2, meia, LARGURA - meia)

        # 2. distância mínima entre os centros = largura de um jogador
        if novo_p2 - novo_p1 < LARGURA_JOGADOR:           # ia sobrepor
            if self.p1.direcao > 0 and self.p2.direcao < 0:
                # um empurrando o outro: ninguém sai do lugar
                novo_p1, novo_p2 = self.p1.x, self.p2.x
            elif self.p1.direcao > 0:
                novo_p1 = novo_p2 - LARGURA_JOGADOR       # P1 encosta em P2
            elif self.p2.direcao < 0:
                novo_p2 = novo_p1 + LARGURA_JOGADOR       # P2 encosta em P1

        self.p1.x, self.p2.x = novo_p1, novo_p2
```

> Observação: nesta versão simples ninguém **empurra** o outro, apenas bloqueia. Se quiser uma versão com empurrão de verdade (quem anda empurra quem está parado), basta mudar o trecho acima.

**Captura e pontuação:**

```python
    def verificar_capturas(self):
        for item in self.itens:
            for jogador in (self.p1, self.p2):
                if colide(item.retangulo(), jogador.retangulo()):
                    if item.tipo == jogador.tipo_alvo:
                        self.pontuacao += PONTOS_ACERTO
                    else:
                        self.pontuacao += PONTOS_ERRO
                    item.ativo = False
                    break
        if PONTUACAO_MINIMA is not None:
            self.pontuacao = max(PONTUACAO_MINIMA, self.pontuacao)

    def remover_itens_inativos(self):
        self.itens = [i for i in self.itens if i.ativo and not i.saiu_da_tela()]
```

Métodos auxiliares de estado: `iniciar()`, `pausar()`, `alternar_pausa()`.

---

## 6. Views (`src/views/`)

> Todas recebem o `GameModel` e **apenas leem** dele.

### `game_view.py`
Desenha o cenário e os objetos. Também faz o "flip" da tela.

```python
class GameView:
    def __init__(self, tela):
        self.tela = tela
        self.hud = HudView(tela)
        self.telas = ScreensView(tela)

    def render(self, model):
        self.tela.fill(COR_FUNDO)
        if model.estado == "MENU":
            self.telas.desenhar_menu()
        else:
            self.desenhar_jogador(model.p1)
            self.desenhar_jogador(model.p2)
            for item in model.itens:
                self.desenhar_item(item)
            self.hud.desenhar(model)
            if model.estado == "PAUSADO": self.telas.desenhar_pausa()
            if model.estado == "FIM":     self.telas.desenhar_fim(model.pontuacao)
        pygame.display.flip()

    def desenhar_jogador(self, p):
        # pygame.draw.polygon com 3 pontos:
        #   topo (p.x, p.y), base esquerda (p.x - w/2, p.y + h), base direita (p.x + w/2, p.y + h)

    def desenhar_item(self, item):
        # se item.tipo == "circulo":  pygame.draw.circle(...)
        # se item.tipo == "quadrado": pygame.draw.rect(...)
```

### `hud_view.py`
Interface durante a partida (texto na tela).

```python
class HudView:
    def desenhar(self, model):
        # - pontuação grande no topo central
        # - tempo restante (canto superior direito)
        # - legenda: "P1 (A/D) pega ●"  e  "P2 (← →) pega ■"
        #   com a cor de cada jogador, para ninguém esquecer o objetivo
```

### `screens_view.py`
Telas estáticas: menu inicial ("Pressione ESPAÇO para começar" + controles), pausa e fim de jogo (pontuação final + "R para reiniciar").

---

## 7. Controllers (`src/controllers/`)

### `input_controller.py`
Traduz teclas em **intenções**. É o único lugar que conhece as teclas.

```python
class InputController:
    def ler_direcoes(self):
        teclas = pygame.key.get_pressed()
        dir_p1 = int(teclas[TECLAS_P1["direita"]]) - int(teclas[TECLAS_P1["esquerda"]])
        dir_p2 = int(teclas[TECLAS_P2["direita"]]) - int(teclas[TECLAS_P2["esquerda"]])
        return dir_p1, dir_p2          # cada um é -1, 0 ou +1

    def tratar_evento(self, evento, model):
        # QUIT          -> retorna False (encerra)
        # ESPAÇO        -> se MENU: model.iniciar()
        # P / ESC       -> model.alternar_pausa()
        # R             -> se FIM: model.reset(); model.iniciar()
```

### `game_controller.py`
O loop principal. Liga Model, View e Input.

```python
class GameController:
    def __init__(self, tela):
        self.model = GameModel()
        self.view = GameView(tela)
        self.input = InputController()
        self.clock = pygame.time.Clock()
        self.rodando = True

    def run(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000        # segundos desde o último frame

            for evento in pygame.event.get():
                if self.input.tratar_evento(evento, self.model) is False:
                    self.rodando = False

            if self.model.estado == "JOGANDO":
                self.model.p1.direcao, self.model.p2.direcao = self.input.ler_direcoes()

            self.model.update(dt)
            self.view.render(self.model)
```

---

## 8. Testes (`tests/`)

Como o Model não depende de janela, dá para testar as regras com `pytest`:

| Arquivo | O que verifica |
|---|---|
| `test_player_movement.py` | Jogador não sai da tela; P1 nunca passa de P2; os dois empurrando um contra o outro não se movem; P2 consegue chegar ao canto esquerdo depois que P1 vai para o canto. |
| `test_scoring.py` | Item certo soma, item errado subtrai, item some após captura, item no chão não altera pontos. |
| `test_spawner.py` | Spawn respeita o intervalo; itens nascem dentro da largura da tela; tipos e cores válidos. |

---

## 9. Ordem sugerida de desenvolvimento

1. **Janela e loop** – `main.py` + `GameController` mostrando uma tela vazia a 60 FPS.
2. **Um jogador** – `Player` + `GameView.desenhar_jogador` + `InputController` (só P1 se movendo).
3. **Dois jogadores + colisão entre eles** – `mover_jogadores` com os 3 casos (parede, bloqueio, empurrão). Teste manual e unitário.
4. **Itens caindo** – `FallingItem` + `ItemSpawner` + desenho de círculo/quadrado.
5. **Captura e pontuação** – `verificar_capturas` + HUD com pontuação.
6. **Estados** – menu, pausa, tempo e tela de fim.
7. **Polimento** – dificuldade progressiva, sons (`pygame.mixer`), feedback visual ao acertar/errar (flash verde/vermelho), recorde.

---

## 10. Ideias extras (opcionais)

- Efeito de "tela piscando" vermelha quando perde ponto.
- Itens especiais (estrela = +5, bomba = -5 para quem pegar).
- Placar de recorde salvo em arquivo `highscore.txt`.
- Modo difícil: itens perdidos também tiram pontos.
- Separar as duas pontuações individuais só para estatística final (quem acertou mais), mantendo a pontuação principal compartilhada.