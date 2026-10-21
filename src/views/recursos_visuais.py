"""Carrega imagens da pasta do projeto e preserva as dimensões lógicas."""

from pathlib import Path

import pygame
from PIL import Image, ImageSequence


class RecursosVisuais:
    def __init__(self, raiz=None):
        self.raiz = Path(raiz) if raiz is not None else Path(__file__).resolve().parents[2]
        self._originais = {}
        self._escaladas = {}
        self._animacoes = {}

    def _imagem(self, caminho):
        if not caminho:
            raise ValueError('Defina IMAGEM na lixeira/fundo ou a imagem no Residuo.')
        absoluto = self.raiz / caminho
        if not absoluto.is_file():
            raise FileNotFoundError(
                f'Imagem não encontrada: {absoluto}. Coloque o arquivo na pasta imagens/ '
                'e ajuste IMAGEM na lixeira/fundo ou o caminho do Residuo.'
            )
        chave = str(absoluto.resolve())
        if chave not in self._originais:
            # GIFs podem vir com paleta de 8 bits; scale exige 24/32 bits.
            imagem = pygame.image.load(chave).convert_alpha()
            if imagem.get_alpha() is not None:
                area = imagem.get_bounding_rect(min_alpha=1)
                if area.width and area.height:
                    imagem = imagem.subsurface(area).copy()
            self._originais[chave] = imagem
        return chave, self._originais[chave]

    def sprite(self, caminho, tamanho):
        chave, original = self._imagem(caminho)
        largura, altura = map(int, tamanho)
        cache = (chave, largura, altura)
        if cache not in self._escaladas:
            escala = min(largura / original.get_width(), altura / original.get_height())
            destino = (max(1, round(original.get_width() * escala)),
                       max(1, round(original.get_height() * escala)))
            self._escaladas[cache] = pygame.transform.scale(original, destino)
        return self._escaladas[cache]

    def fundo(self, caminho, tamanho):
        if caminho and Path(caminho).suffix.lower() == '.gif':
            return self._quadro_gif(caminho, tamanho)

        chave, original = self._imagem(caminho)
        largura, altura = map(int, tamanho)
        cache = (chave, largura, altura, 'fundo')
        if cache not in self._escaladas:
            self._escaladas[cache] = pygame.transform.scale(original, (largura, altura))
        return self._escaladas[cache]

    def _quadro_gif(self, caminho, tamanho):
        absoluto = self.raiz / caminho
        if not absoluto.is_file():
            raise FileNotFoundError(
                f'Imagem não encontrada: {absoluto}. Coloque o arquivo na pasta imagens/ '
                'e ajuste IMAGEM na lixeira/fundo ou o caminho do Residuo.'
            )

        chave = str(absoluto.resolve())
        if chave not in self._animacoes:
            quadros = []
            duracoes = []
            with Image.open(chave) as gif:
                for quadro in ImageSequence.Iterator(gif):
                    imagem = quadro.convert('RGBA')
                    superficie = pygame.image.frombytes(
                        imagem.tobytes(), imagem.size, 'RGBA'
                    ).convert_alpha()
                    quadros.append(superficie)
                    duracoes.append(max(1, int(quadro.info.get('duration', 100))))
            self._animacoes[chave] = (quadros, duracoes, sum(duracoes))

        quadros, duracoes, duracao_total = self._animacoes[chave]
        tempo = pygame.time.get_ticks() % duracao_total
        for indice, duracao in enumerate(duracoes):
            if tempo < duracao:
                break
            tempo -= duracao

        largura, altura = map(int, tamanho)
        cache = (chave, largura, altura, 'fundo', indice)
        if cache not in self._escaladas:
            self._escaladas[cache] = pygame.transform.scale(
                quadros[indice], (largura, altura)
            )
        return self._escaladas[cache]

    def desenhar(self, tela, caminho, retangulo, ancora='centro'):
        imagem = self.sprite(caminho, retangulo.size)
        destino = imagem.get_rect()
        if ancora == 'centro_base':
            destino.midbottom = retangulo.midbottom
        else:
            destino.center = retangulo.center
        tela.blit(imagem, destino)
