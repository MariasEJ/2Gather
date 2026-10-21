"""Carrega imagens da pasta do projeto e preserva as dimensões lógicas."""

from pathlib import Path

import pygame


class RecursosVisuais:
    def __init__(self, raiz=None):
        self.raiz = Path(raiz) if raiz is not None else Path(__file__).resolve().parents[2]
        self._originais = {}
        self._escaladas = {}

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
            # GIFs podem vir com paleta de 8 bits; smoothscale exige 24/32 bits.
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
            self._escaladas[cache] = pygame.transform.smoothscale(original, destino)
        return self._escaladas[cache]

    def fundo(self, caminho, tamanho):
        chave, original = self._imagem(caminho)
        largura, altura = map(int, tamanho)
        cache = (chave, largura, altura, 'fundo')
        if cache not in self._escaladas:
            self._escaladas[cache] = pygame.transform.smoothscale(original, (largura, altura))
        return self._escaladas[cache]

    def desenhar(self, tela, caminho, retangulo, ancora='centro'):
        imagem = self.sprite(caminho, retangulo.size)
        destino = imagem.get_rect()
        if ancora == 'centro_base':
            destino.midbottom = retangulo.midbottom
        else:
            destino.center = retangulo.center
        tela.blit(imagem, destino)
