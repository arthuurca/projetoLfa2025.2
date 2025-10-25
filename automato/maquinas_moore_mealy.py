# Arquivo: simulador_de_automatos/automato/maquinas_moore_mealy.py
from .automato_finito import AutomatoFinito
from .estado import Estado
from automato import EPSILON

# -----------------
# MÁQUINA DE MOORE
# -----------------
class MaquinaMoore(AutomatoFinito):
    """
    Máquina de Moore: A saída é associada ao estado.
    """
    def adicionar_estado(self, nome, x, y, output="", is_final=False, is_inicial=False):
        """
        Adiciona um estado com um símbolo de saída associado.
        """
        if nome in self.estados:
            raise ValueError(f"Estado '{nome}' já existe.")
        # Note que o output é passado para o objeto Estado
        novo_estado = Estado(nome, x, y, is_final, is_inicial, output=output)
        self.estados[nome] = novo_estado
        if is_inicial:
            self.definir_estado_inicial(nome)
        if is_final:
            self.alternar_estado_final(nome)

    def adicionar_transicao(self, origem, simbolo, destino):
        """
        Transição da Moore é igual à do AFD.
        (origem, simbolo) -> destino
        """
        if origem in self.estados and destino in self.estados:
            self.transicoes[(origem, simbolo)] = destino
            if simbolo != EPSILON: self.alfabeto.add(simbolo)
    
    def set_output_estado(self, nome_estado, output):
        """
        Define a saída de um estado específico.
        """
        if nome_estado not in self.estados:
            raise ValueError(f"Estado '{nome_estado}' não encontrado.")
        self.estados[nome_estado].output = output


# -----------------
# MÁQUINA DE MEALY
# -----------------
class MaquinaMealy(AutomatoFinito):
    """
    Máquina de Mealy: A saída é associada à transição.
    """
    def adicionar_transicao(self, origem, simbolo, destino, output):
        """
        Adiciona uma transição onde a saída está incluída.
        (origem, simbolo) -> (destino, output)
        """
        if origem in self.estados and destino in self.estados:
            self.transicoes[(origem, simbolo)] = (destino, output)
            if simbolo != EPSILON: self.alfabeto.add(simbolo)
    
    # --- Overrides para lidar com o formato de transição (destino, output) ---
    
    def renomear_estado(self, nome_antigo, nome_novo):
        if nome_novo in self.estados and nome_antigo != nome_novo:
            raise ValueError(f"O nome '{nome_novo}' já está em uso.")
        if nome_antigo not in self.estados:
            raise ValueError(f"Estado '{nome_antigo}' não encontrado.")

        estado_obj = self.estados.pop(nome_antigo)
        estado_obj.nome = nome_novo
        self.estados[nome_novo] = estado_obj

        novas_transicoes = {}
        for (origem, simbolo), (destino, output) in self.transicoes.items():
            nova_origem = nome_novo if origem == nome_antigo else origem
            novo_destino = nome_novo if destino == nome_antigo else destino
            novas_transicoes[(nova_origem, simbolo)] = (novo_destino, output)
            
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_novo:
            self.estado_inicial = estado_obj
        # estados_finais é um set de objetos Estado, que já foi atualizado
        # (não precisamos mexer nele)

    def deletar_estado(self, nome_estado):
        if nome_estado not in self.estados: return
        estado_a_deletar = self.estados[nome_estado]

        novas_transicoes = {}
        for chave, (destino, output) in self.transicoes.items():
            origem, simbolo = chave
            if origem == nome_estado or destino == nome_estado:
                continue
            novas_transicoes[chave] = (destino, output)
        self.transicoes = novas_transicoes

        if self.estado_inicial and self.estado_inicial.nome == nome_estado: self.estado_inicial = None
        if estado_a_deletar in self.estados_finais: self.estados_finais.remove(estado_a_deletar)
        del self.estados[nome_estado]

    def deletar_transicoes_entre(self, origem, destino):
        chaves_para_remover = []
        for chave, (d_real, output) in self.transicoes.items():
            o_real, s = chave
            if o_real == origem and d_real == destino:
                chaves_para_remover.append(chave)
        
        for chave in chaves_para_remover:
            if chave in self.transicoes:
                del self.transicoes[chave]