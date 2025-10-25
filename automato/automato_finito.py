from .estado import Estado
from automato import EPSILON # Importa EPSILON do __init__

class AutomatoFinito:
    def __init__(self):
        self.estados = {}
        self.alfabeto = set()
        self.transicoes = {} # Dicionário: (estado_origem, simbolo) -> set(estados_destino) ou estado_destino (AFD)
        self.estado_inicial = None # ATRIBUTO CORRETO
        self.estados_finais = set()

    def adicionar_estado(self, nome, x, y, is_final=False, is_inicial=False):
        if nome in self.estados:
            raise ValueError(f"Estado '{nome}' já existe.")
        novo_estado = Estado(nome, x, y, is_final, is_inicial)
        self.estados[nome] = novo_estado
        if is_inicial:
            self.definir_estado_inicial(nome)
        if is_final:
            self.alternar_estado_final(nome) # Usa alternar aqui para adicionar ao set

    def renomear_estado(self, nome_antigo, nome_novo):
        if nome_novo in self.estados and nome_antigo != nome_novo:
            raise ValueError(f"O nome '{nome_novo}' já está em uso.")
        if nome_antigo not in self.estados:
            raise ValueError(f"Estado '{nome_antigo}' não encontrado.")

        estado_obj = self.estados.pop(nome_antigo)
        estado_obj.nome = nome_novo
        self.estados[nome_novo] = estado_obj

        novas_transicoes = {}
        for (origem, simbolo), destino_set in self.transicoes.items():
            nova_origem = nome_novo if origem == nome_antigo else origem

            if isinstance(destino_set, set): # AFN
                novo_destino_set = {nome_novo if d == nome_antigo else d for d in destino_set}
                novas_transicoes[(nova_origem, simbolo)] = novo_destino_set
            else: # AFD
                novo_destino = nome_novo if destino_set == nome_antigo else destino_set
                novas_transicoes[(nova_origem, simbolo)] = novo_destino
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_novo:
             self.estado_inicial = estado_obj


    def definir_estado_inicial(self, nome_estado):
        if nome_estado not in self.estados:
             raise ValueError(f"Estado '{nome_estado}' não existe para definir como inicial.")
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
            if estado.is_final: self.estados_finais.add(estado)
            elif estado in self.estados_finais: self.estados_finais.remove(estado)

    def deletar_estado(self, nome_estado):
        if nome_estado not in self.estados: return
        estado_a_deletar = self.estados[nome_estado]

        novas_transicoes = {}
        for chave, destinos in self.transicoes.items():
            origem, simbolo = chave
            if origem == nome_estado: continue

            if isinstance(destinos, set): # AFN
                novos_destinos = destinos - {nome_estado}
                if novos_destinos: novas_transicoes[chave] = novos_destinos
            else: # AFD
                if destinos != nome_estado: novas_transicoes[chave] = destinos
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_estado: self.estado_inicial = None
        if estado_a_deletar in self.estados_finais: self.estados_finais.remove(estado_a_deletar)
        del self.estados[nome_estado]

    def deletar_transicoes_entre(self, origem, destino):
        chaves_para_remover = []
        chaves_para_modificar = {}

        for chave, destinos_reais in self.transicoes.items():
            o, s = chave
            if o == origem:
                if isinstance(destinos_reais, set):
                    if destino in destinos_reais:
                        if chave not in chaves_para_modificar: chaves_para_modificar[chave] = set()
                        chaves_para_modificar[chave].add(destino)
                else:
                    if destinos_reais == destino: chaves_para_remover.append(chave)

        for chave in chaves_para_remover:
            if chave in self.transicoes: del self.transicoes[chave]
        for chave, destinos_a_remover in chaves_para_modificar.items():
             if chave in self.transicoes:
                 self.transicoes[chave].difference_update(destinos_a_remover)
                 if not self.transicoes[chave]: del self.transicoes[chave]


class AFD(AutomatoFinito):
    def adicionar_transicao(self, origem, simbolo, destino):
        if origem in self.estados and destino in self.estados:
            self.transicoes[(origem, simbolo)] = destino
            if simbolo != EPSILON: self.alfabeto.add(simbolo)

class AFN(AutomatoFinito):
    def adicionar_transicao(self, origem, simbolo, destino):
        if origem in self.estados and destino in self.estados:
            chave = (origem, simbolo)
            if chave not in self.transicoes: self.transicoes[chave] = set()
            elif not isinstance(self.transicoes[chave], set): self.transicoes[chave] = {self.transicoes[chave]}
            self.transicoes[chave].add(destino)
            if simbolo != EPSILON: self.alfabeto.add(simbolo)

    def fecho_epsilon(self, estados_nomes):
        pilha = list(estados_nomes)
        fecho = set(estados_nomes)
        while pilha:
            estado_nome = pilha.pop()
            chave_epsilon = (estado_nome, EPSILON)
            if chave_epsilon in self.transicoes:
                destinos_epsilon = self.transicoes[chave_epsilon]
                if isinstance(destinos_epsilon, set):
                    for vizinho in destinos_epsilon:
                        if vizinho not in fecho: fecho.add(vizinho); pilha.append(vizinho)
                elif destinos_epsilon not in fecho: fecho.add(destinos_epsilon); pilha.append(destinos_epsilon)
        return fecho