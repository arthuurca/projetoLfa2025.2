from .estado import Estado
from automato import EPSILON # Importa EPSILON

class AutomatoPilha:
    def __init__(self):
        self.estados = {}
        self.transicoes = {}
        self.estado_inicial = None
        self.estados_finais = set()
        self.simbolo_inicial_pilha = 'Z'

    def adicionar_estado(self, nome, x, y, is_final=False, is_inicial=False):
        if nome in self.estados: raise ValueError(f"Estado '{nome}' já existe.")
        self.estados[nome] = Estado(nome, x, y, is_final, is_inicial)
        if is_inicial: self.definir_estado_inicial(nome)
        if is_final: self.alternar_estado_final(nome)

    def renomear_estado(self, nome_antigo, nome_novo):
        if nome_novo in self.estados and nome_antigo != nome_novo:
            raise ValueError(f"O nome '{nome_novo}' já está em uso.")
        if nome_antigo not in self.estados:
            raise ValueError(f"Estado '{nome_antigo}' não encontrado.")

        estado_obj = self.estados.pop(nome_antigo)
        estado_obj.nome = nome_novo
        self.estados[nome_novo] = estado_obj

        novas_transicoes = {}
        for (origem, s_in, s_pop), destinos_set in self.transicoes.items():
            nova_origem = nome_novo if origem == nome_antigo else origem
            novo_destinos_set = set()
            for destino, s_push in destinos_set:
                 novo_destino = nome_novo if destino == nome_antigo else destino
                 novo_destinos_set.add((novo_destino, s_push))
            novas_transicoes[(nova_origem, s_in, s_pop)] = novo_destinos_set
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
                     if state_obj == self.estado_inicial: state_obj.is_inicial = False; break
        self.estado_inicial = self.estados[nome_estado]; self.estados[nome_estado].is_inicial = True

    def alternar_estado_final(self, nome_estado):
        if nome_estado in self.estados:
            estado = self.estados[nome_estado]
            estado.is_final = not estado.is_final
            if estado.is_final: self.estados_finais.add(estado)
            elif estado in self.estados_finais: self.estados_finais.remove(estado)

    def adicionar_transicao(self, origem, s_in, s_pop, destino, s_push):
        if origem not in self.estados or destino not in self.estados:
            raise ValueError("Estado de origem ou destino inválido para transição de pilha.")
        chave = (origem, s_in, s_pop)
        if chave not in self.transicoes: self.transicoes[chave] = set()
        self.transicoes[chave].add((destino, s_push))

    def deletar_estado(self, nome_estado):
        if nome_estado not in self.estados: return
        estado_a_deletar = self.estados[nome_estado]

        novas_transicoes = {}
        for chave, destinos_set in self.transicoes.items():
            origem, s_in, s_pop = chave
            if origem == nome_estado: continue
            novo_destinos_set = {(d, p) for d, p in destinos_set if d != nome_estado}
            if novo_destinos_set: novas_transicoes[chave] = novo_destinos_set
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_estado: self.estado_inicial = None
        if estado_a_deletar in self.estados_finais: self.estados_finais.remove(estado_a_deletar)
        del self.estados[nome_estado]

    def deletar_transicoes_entre(self, origem, destino):
        chaves_para_remover = []
        chaves_para_modificar = {}

        for chave, destinos_set in self.transicoes.items():
             o, _, _ = chave
             if o == origem:
                 remover_deste_set = set()
                 for d, p in destinos_set:
                     if d == destino: remover_deste_set.add((d,p))
                 if remover_deste_set:
                     if chave not in chaves_para_modificar: chaves_para_modificar[chave] = set()
                     chaves_para_modificar[chave].update(remover_deste_set)

        for chave, remover_set in chaves_para_modificar.items():
             if chave in self.transicoes:
                 self.transicoes[chave].difference_update(remover_set)
                 if not self.transicoes[chave]: chaves_para_remover.append(chave)
        for chave in chaves_para_remover:
            if chave in self.transicoes: del self.transicoes[chave]