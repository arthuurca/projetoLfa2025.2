# Arquivo: simulador_de_automatos/automato/maquina_turing.py
from .estado import Estado
from automato import EPSILON

class MaquinaTuring:
    """
    Máquina de Turing (Determinística, 1 fita).
    """
    def __init__(self, simbolo_branco='B'):
        self.estados = {}
        # (origem, lido) -> (destino, escrito, direcao)
        self.transicoes = {}
        self.estado_inicial = None
        self.estados_finais = set()
        self.simbolo_branco = simbolo_branco

    def adicionar_estado(self, nome, x, y, is_final=False, is_inicial=False):
        if nome in self.estados:
            raise ValueError(f"Estado '{nome}' já existe.")
        # Reutiliza o objeto Estado (sem output)
        novo_estado = Estado(nome, x, y, is_final, is_inicial)
        self.estados[nome] = novo_estado
        if is_inicial:
            self.definir_estado_inicial(nome)
        if is_final:
            self.alternar_estado_final(nome)

    def adicionar_transicao(self, origem, lido, destino, escrito, direcao):
        """
        Adiciona uma transição da MT.
        Direção deve ser 'R' (Direita) ou 'L' (Esquerda).
        """
        if origem not in self.estados or destino not in self.estados:
            raise ValueError("Estado de origem ou destino inválido.")
        if direcao not in ['R', 'L']:
            raise ValueError("Direção deve ser 'R' ou 'L'.")
        
        self.transicoes[(origem, lido)] = (destino, escrito, direcao)

    def definir_estado_inicial(self, nome_estado):
        if nome_estado not in self.estados:
            raise ValueError(f"Estado '{nome_estado}' não existe.")
        if self.estado_inicial:
            if self.estado_inicial.nome in self.estados:
                self.estados[self.estado_inicial.nome].is_inicial = False
            else:
                for state_obj in self.estados.values():
                    if state_obj == self.estado_inicial:
                        state_obj.is_inicial = False
                        break
        self.estado_inicial = self.estados[nome_estado]
        self.estados[nome_estado].is_inicial = True

    def alternar_estado_final(self, nome_estado):
        if nome_estado in self.estados:
            estado = self.estados[nome_estado]
            estado.is_final = not estado.is_final
            if estado.is_final:
                self.estados_finais.add(estado)
            elif estado in self.estados_finais:
                self.estados_finais.remove(estado)

    def renomear_estado(self, nome_antigo, nome_novo):
        if nome_novo in self.estados and nome_antigo != nome_novo:
            raise ValueError(f"O nome '{nome_novo}' já está em uso.")
        if nome_antigo not in self.estados:
            raise ValueError(f"Estado '{nome_antigo}' não encontrado.")

        estado_obj = self.estados.pop(nome_antigo)
        estado_obj.nome = nome_novo
        self.estados[nome_novo] = estado_obj

        novas_transicoes = {}
        for (origem, lido), (destino, escrito, direcao) in self.transicoes.items():
            nova_origem = nome_novo if origem == nome_antigo else origem
            novo_destino = nome_novo if destino == nome_antigo else destino
            novas_transicoes[(nova_origem, lido)] = (novo_destino, escrito, direcao)
            
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_novo:
            self.estado_inicial = estado_obj

    def deletar_estado(self, nome_estado):
        if nome_estado not in self.estados: return
        estado_a_deletar = self.estados[nome_estado]

        novas_transicoes = {}
        for chave, (destino, escrito, direcao) in self.transicoes.items():
            origem, lido = chave
            if origem == nome_estado or destino == nome_estado:
                continue
            novas_transicoes[chave] = (destino, escrito, direcao)
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_estado: self.estado_inicial = None
        if estado_a_deletar in self.estados_finais: self.estados_finais.remove(estado_a_deletar)
        del self.estados[nome_estado]

    def deletar_transicoes_entre(self, origem, destino):
        chaves_para_remover = []
        for chave, (d_real, esc, dir) in self.transicoes.items():
            o_real, s = chave
            if o_real == origem and d_real == destino:
                chaves_para_remover.append(chave)
        
        for chave in chaves_para_remover:
            if chave in self.transicoes:
                del self.transicoes[chave]