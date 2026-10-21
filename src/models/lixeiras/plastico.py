"""Lixeira de plástico e resíduos que podem ser descartados nela."""

from src.models.lixeiras.base import Lixeira, Residuo


class LixeiraPlastico(Lixeira):
    ID = 'plastico'
    NOME = 'PLÁSTICO'
    IMAGEM = 'imagens/lixeira-rec-plastico.png'
    ITENS = (
        Residuo('plastico_pet1', 'Garrafa PET Agua', 'imagens/garrafa1.png', tamanho=(32, 32)),
        Residuo('plastico_pet2', 'Garrafa PET Refrigerante', 'imagens/coquinha.png', tamanho=(32, 32)),
        Residuo('plastico_frasco', 'Frasco plástico', 'imagens/qboinha.png', tamanho=(32, 32)),
        Residuo('plastico_cd', 'CD', 'imagens/cd-lixo1.png', tamanho=(32, 32)),
    )
