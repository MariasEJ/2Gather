"""Lixeira de plástico e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraPlastico(Lixeira):
    ID = 'plastico'
    NOME = 'PLÁSTICO'
    IMAGEM = 'imagens/lixeira-rec-plastico.png'
    ITENS = (
        Residuo('plastico_pet1', 'Garrafa PET Agua', 'imagens/garrafa1.png', tamanho=(64, 64)),
        Residuo('plastico_pet2', 'Garrafa PET Refrigerante', 'imagens/coquinha.png', tamanho=(84, 84)),
        Residuo('plastico_frasco', 'Frasco plástico', 'imagens/qboinha.png', tamanho=(64, 64)),
        Residuo('plastico_cd', 'CD', 'imagens/cd-lixo1.png', tamanho=(64, 64)),
        Residuo('plastico_sacola', 'Sacola plástica', 'imagens/sacola.png', tamanho=(64, 64))
    )
