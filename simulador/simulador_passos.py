# Arquivo: simulador_de_automatos/simulador/simulador_passos.py
from automato import EPSILON
from collections import defaultdict
import time

class SimuladorPassos:
    def __init__(self, automato, cadeia):
        self.automato = automato
        self.cadeia_original = cadeia
        self.gerador = self._criar_gerador()

    def proximo_passo(self):
        try:
            return next(self.gerador)
        except StopIteration:
            return None

    def _criar_gerador(self):
        raise NotImplementedError("Subclasses devem implementar este método.")

# --- Simuladores AFN/AFD (Sem mudança) ---

class SimuladorAFD(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estado_atual = self.automato.estado_inicial.nome
        cadeia_restante = self.cadeia_original

        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": set()}

        for i, simbolo in enumerate(self.cadeia_original):
            chave = (estado_atual, simbolo)
            if chave in self.automato.transicoes:
                estado_origem = estado_atual
                estado_atual = self.automato.transicoes[chave]
                cadeia_restante = self.cadeia_original[i+1:]
                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": {(estado_origem, estado_atual)}}
            else:
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, {simbolo})."}; return

        if estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
            yield {"status": "aceita", "mensagem": "Cadeia aceita!"}
        else:
            yield {"status": "rejeita", "mensagem": "Parou em estado não final."}

class SimuladorAFN(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estados_atuais = self.automato.fecho_epsilon({self.automato.estado_inicial.nome})
        cadeia_restante = self.cadeia_original

        yield {"status": "executando", "estado_atual": estados_atuais, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": set()}

        for i, simbolo in enumerate(self.cadeia_original):
            transicoes_ativas_simbolo = set()
            proximos_estados_sem_fecho = set()

            for estado_origem in estados_atuais:
                chave = (estado_origem, simbolo)
                if chave in self.automato.transicoes:
                    destinos = self.automato.transicoes[chave]
                    if isinstance(destinos, set):
                        for estado_destino in destinos:
                            proximos_estados_sem_fecho.add(estado_destino)
                            transicoes_ativas_simbolo.add((estado_origem, estado_destino))
                    else:
                        proximos_estados_sem_fecho.add(destinos)
                        transicoes_ativas_simbolo.add((estado_origem, destinos))

            if not proximos_estados_sem_fecho:
                yield {"status": "rejeita", "mensagem": f"Nenhuma transição para o símbolo '{simbolo}' a partir dos estados atuais."}; return

            estados_apos_fecho = self.automato.fecho_epsilon(proximos_estados_sem_fecho)
            estados_atuais = estados_apos_fecho
            cadeia_restante = self.cadeia_original[i+1:]

            yield {"status": "executando", "estado_atual": estados_atuais, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": transicoes_ativas_simbolo}

        aceita = any(self.automato.estados[e] in self.automato.estados_finais for e in estados_atuais if e in self.automato.estados)
        if aceita:
            yield {"status": "aceita", "mensagem": "Cadeia aceita!"}
        else:
            yield {"status": "rejeita", "mensagem": "Nenhum estado final foi alcançado."}

# --- Simulador AP (Sem mudança) ---
class SimuladorAP(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        configs = [(self.automato.estado_inicial.nome, 0, [self.automato.simbolo_inicial_pilha], None)]
        visitados_ciclo = set()
        max_steps = 1000
        steps = 0

        while configs and steps < max_steps:
            estado_atual, indice_cadeia, pilha, transicao_anterior = configs.pop(0) # BFS
            steps += 1

            config_tupla = (estado_atual, indice_cadeia, tuple(pilha))
            if config_tupla in visitados_ciclo: continue
            visitados_ciclo.add(config_tupla)

            cadeia_restante = self.cadeia_original[indice_cadeia:]

            yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "pilha": ''.join(pilha), "transicao_ativa": transicao_anterior}

            if indice_cadeia == len(self.cadeia_original) and estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
                yield {"status": "aceita", "mensagem": "Cadeia aceita por estado final!"}; return

            simbolo_entrada = self.cadeia_original[indice_cadeia] if indice_cadeia < len(self.cadeia_original) else EPSILON
            topo_pilha = pilha[-1] if pilha else EPSILON

            possibilidades = []
            if simbolo_entrada != EPSILON and topo_pilha != EPSILON:
                chave = (estado_atual, simbolo_entrada, topo_pilha)
                if chave in self.automato.transicoes: possibilidades.append({'chave': chave, 'consome_entrada': True, 'consome_pilha': True})
            if simbolo_entrada != EPSILON:
                chave = (estado_atual, simbolo_entrada, EPSILON)
                if chave in self.automato.transicoes: possibilidades.append({'chave': chave, 'consome_entrada': True, 'consome_pilha': False})
            if topo_pilha != EPSILON:
                chave = (estado_atual, EPSILON, topo_pilha)
                if chave in self.automato.transicoes: possibilidades.append({'chave': chave, 'consome_entrada': False, 'consome_pilha': True})
            chave = (estado_atual, EPSILON, EPSILON)
            if chave in self.automato.transicoes: possibilidades.append({'chave': chave, 'consome_entrada': False, 'consome_pilha': False})

            for p in possibilidades:
                chave_transicao = p['chave']
                for destino, simbolos_push in self.automato.transicoes[chave_transicao]:
                    nova_pilha = list(pilha)
                    if p['consome_pilha']:
                        if not nova_pilha: continue
                        nova_pilha.pop()
                    if simbolos_push != EPSILON:
                        for char in reversed(simbolos_push): nova_pilha.append(char)
                    novo_indice = indice_cadeia + 1 if p['consome_entrada'] else indice_cadeia
                    if steps < max_steps:
                        configs.append((destino, novo_indice, nova_pilha, {(estado_atual, destino)}))

        if steps >= max_steps:
            yield {"status": "rejeita", "mensagem": "Simulação interrompida (limite de passos atingido - possível loop infinito)."}
        else:
            yield {"status": "rejeita", "mensagem": "Nenhum caminho levou a um estado de aceitação."}

# --- NOVOS SIMULADORES ---

class SimuladorMoore(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return
        if self.automato.estado_inicial.nome not in self.automato.estados:
             yield {"status": "erro", "mensagem": "Estado inicial não existe mais."}; return

        estado_atual = self.automato.estado_inicial.nome
        cadeia_restante = self.cadeia_original
        # Saída de Moore: começa com a saída do estado inicial
        output_str = self.automato.estados[estado_atual].output or ""

        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": set()}

        for i, simbolo in enumerate(self.cadeia_original):
            chave = (estado_atual, simbolo)
            if chave in self.automato.transicoes:
                estado_origem = estado_atual
                estado_atual = self.automato.transicoes[chave]
                cadeia_restante = self.cadeia_original[i+1:]
                # Adiciona a saída do *novo* estado
                output_str += self.automato.estados[estado_atual].output or ""
                
                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": {(estado_origem, estado_atual)}}
            else:
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, {simbolo}).", "output": output_str}; return

        # Moore não "aceita" ou "rejeita", apenas termina
        yield {"status": "finalizado", "mensagem": "Cadeia processada.", "output": output_str}

class SimuladorMealy(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estado_atual = self.automato.estado_inicial.nome
        cadeia_restante = self.cadeia_original
        output_str = "" # Saída de Mealy começa vazia

        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": set()}

        for i, simbolo in enumerate(self.cadeia_original):
            chave = (estado_atual, simbolo)
            if chave in self.automato.transicoes:
                estado_origem = estado_atual
                # Transição de Mealy retorna (destino, output)
                estado_atual, output_transicao = self.automato.transicoes[chave]
                cadeia_restante = self.cadeia_original[i+1:]
                # Adiciona a saída da *transição*
                output_str += output_transicao or ""
                
                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": {(estado_origem, estado_atual)}}
            else:
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, {simbolo}).", "output": output_str}; return

        yield {"status": "finalizado", "mensagem": "Cadeia processada.", "output": output_str}

class SimuladorMT(SimuladorPassos):
    
    def _visualizar_fita(self, tape, head, window=20):
        """Helper para criar uma string da fita."""
        min_idx = min(tape.keys()) if tape else 0
        max_idx = max(tape.keys()) if tape else 0
        
        # Define a janela de visualização ao redor do cabeçote
        start = max(min(min_idx, head - window), head - window)
        end = min(max(max_idx, head + window), head + window)
        
        fita_str = ""
        for i in range(start, end + 1):
            simbolo = tape.get(i, self.automato.simbolo_branco)
            if i == head:
                fita_str += f"[{simbolo}]" # Destaca o cabeçote
            else:
                fita_str += f" {simbolo} "
        return fita_str.strip()

    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        fita = defaultdict(lambda: self.automato.simbolo_branco)
        for i, s in enumerate(self.cadeia_original):
            fita[i] = s
        
        cabecote = 0
        estado_atual = self.automato.estado_inicial.nome
        max_steps = 2000
        steps = 0
        
        while steps < max_steps:
            steps += 1
            fita_str = self._visualizar_fita(fita, cabecote)
            
            # Checa se parou
            if estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
                yield {"status": "aceita", "mensagem": "Cadeia aceita!", "estado_atual": {estado_atual}, "tape": fita_str, "transicao_ativa": set()}; return

            simbolo_lido = fita[cabecote]
            chave_transicao = (estado_atual, simbolo_lido)

            yield {"status": "executando", "estado_atual": {estado_atual}, "tape": fita_str, "transicao_ativa": set()} # Transição será destacada no próximo passo

            if chave_transicao not in self.automato.transicoes:
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, {simbolo_lido}).", "estado_atual": {estado_atual}, "tape": fita_str}; return

            # Executa a transição
            estado_origem = estado_atual
            (prox_estado, simbolo_escrito, direcao) = self.automato.transicoes[chave_transicao]
            
            fita[cabecote] = simbolo_escrito
            
            if direcao == 'R':
                cabecote += 1
            elif direcao == 'L':
                cabecote -= 1
                
            estado_atual = prox_estado
            
            # Yield extra para mostrar a transição que acabou de ocorrer
            fita_str_apos = self._visualizar_fita(fita, cabecote)
            yield {"status": "executando", "estado_atual": {estado_atual}, "tape": fita_str_apos, "transicao_ativa": {(estado_origem, estado_atual)}}


        if steps >= max_steps:
            yield {"status": "rejeita", "mensagem": "Simulação interrompida (limite de passos atingido)."}