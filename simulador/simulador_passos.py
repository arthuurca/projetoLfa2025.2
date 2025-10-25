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

# --- Simulador AFD (CORRIGIDO para múltiplos caracteres) ---
class SimuladorAFD(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estado_atual = self.automato.estado_inicial.nome
        indice_atual = 0 # Usaremos um índice em vez de enumerate

        # Estado inicial
        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": self.cadeia_original[indice_atual:], "pilha": None, "transicao_ativa": set()}

        while indice_atual < len(self.cadeia_original):
            cadeia_restante_a_partir_do_indice = self.cadeia_original[indice_atual:]
            transicao_encontrada = None
            rotulo_consumido = ""
            proximo_estado = ""

            # Procura a transição que casa com o início da cadeia restante
            # Ordena por comprimento decrescente para priorizar rótulos mais longos (ex: "aa" antes de "a")
            transicoes_possiveis = sorted(
                [(chave, destino) for chave, destino in self.automato.transicoes.items() if chave[0] == estado_atual],
                key=lambda item: len(item[0][1]), # Chave é (origem, rotulo)
                reverse=True
            )

            for (origem, rotulo), destino in transicoes_possiveis:
                 # Ignora transição épsilon aqui, AFD não deveria ter explicitamente
                 # Se tiver, precisa de lógica adicional, mas geralmente não se usa em AFD puro
                if rotulo != EPSILON and cadeia_restante_a_partir_do_indice.startswith(rotulo):
                    transicao_encontrada = (origem, destino)
                    rotulo_consumido = rotulo
                    proximo_estado = destino
                    break # Encontrou a única transição possível para AFD

            if transicao_encontrada:
                estado_origem = estado_atual
                estado_atual = proximo_estado
                indice_atual += len(rotulo_consumido) # Avança o índice pelo tamanho do rótulo
                cadeia_restante = self.cadeia_original[indice_atual:]

                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": {transicao_encontrada}}
            else:
                # Nenhuma transição válida encontrada
                simbolo_atual_falha = self.cadeia_original[indice_atual] if indice_atual < len(self.cadeia_original) else "fim da cadeia"
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, começando com '{simbolo_atual_falha}').", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante_a_partir_do_indice}; return

        # Após o loop, verifica o estado final
        if estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
            yield {"status": "aceita", "mensagem": "Cadeia aceita!", "estado_atual": {estado_atual}, "cadeia_restante": ""}
        else:
            yield {"status": "rejeita", "mensagem": "Parou em estado não final.", "estado_atual": {estado_atual}, "cadeia_restante": ""}


# --- Simulador AFN (CORRIGIDO para múltiplos caracteres) ---
class SimuladorAFN(SimuladorPassos):
    def _criar_gerador(self):
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estados_atuais = self.automato.fecho_epsilon({self.automato.estado_inicial.nome})
        indice_atual = 0 # Usaremos índice

        yield {"status": "executando", "estado_atual": estados_atuais, "cadeia_restante": self.cadeia_original[indice_atual:], "pilha": None, "transicao_ativa": set()}

        while indice_atual < len(self.cadeia_original):
            proximos_estados_sem_fecho = set()
            transicoes_ativas_passo = set()
            rotulo_mais_longo_consumido = "" # Para saber quanto avançar na cadeia

            cadeia_restante_a_partir_do_indice = self.cadeia_original[indice_atual:]
            
            # --- Encontra todas as transições possíveis (não-epsilon) que casam com o início da cadeia ---
            transicoes_possiveis_neste_passo = []
            for estado_origem in estados_atuais:
                for (origem, rotulo), destinos in self.automato.transicoes.items():
                    # Considera apenas transições não-epsilon que partem dos estados atuais
                    # e que casam com o início da cadeia restante
                    if origem == estado_origem and rotulo != EPSILON and cadeia_restante_a_partir_do_indice.startswith(rotulo):
                         transicoes_possiveis_neste_passo.append({
                             "origem": origem,
                             "rotulo": rotulo,
                             "destinos": destinos if isinstance(destinos, set) else {destinos}
                         })
            
            if not transicoes_possiveis_neste_passo:
                 # Se não há transições normais, a cadeia pode ter acabado ou travado
                 break # Sai do loop principal para verificar aceitação

            # Encontra o comprimento do rótulo mais longo que casou
            # Isso é crucial para consumir a quantidade correta da cadeia
            len_rotulo_mais_longo = max(len(t["rotulo"]) for t in transicoes_possiveis_neste_passo)
            rotulo_mais_longo_consumido = self.cadeia_original[indice_atual : indice_atual + len_rotulo_mais_longo] # Guarda para debug/info se precisar
            
            # Executa apenas as transições que usam o rótulo do comprimento máximo encontrado
            for t in transicoes_possiveis_neste_passo:
                if len(t["rotulo"]) == len_rotulo_mais_longo:
                    for estado_destino in t["destinos"]:
                        proximos_estados_sem_fecho.add(estado_destino)
                        transicoes_ativas_passo.add((t["origem"], estado_destino))

            if not proximos_estados_sem_fecho:
                 # Isso não deveria acontecer se transicoes_possiveis_neste_passo não for vazio
                 simbolo_atual_falha = self.cadeia_original[indice_atual] if indice_atual < len(self.cadeia_original) else "fim da cadeia"
                 yield {"status": "rejeita", "mensagem": f"Nenhuma transição válida a partir dos estados {estados_atuais} para '{simbolo_atual_falha}'."}; return

            # Aplica fecho-epsilon aos estados alcançados
            estados_apos_fecho = self.automato.fecho_epsilon(proximos_estados_sem_fecho)
            estados_atuais = estados_apos_fecho
            indice_atual += len_rotulo_mais_longo # Avança o índice pelo tamanho do rótulo consumido
            cadeia_restante = self.cadeia_original[indice_atual:]

            yield {"status": "executando", "estado_atual": estados_atuais, "cadeia_restante": cadeia_restante, "pilha": None, "transicao_ativa": transicoes_ativas_passo}
            # --- Fim da Lógica ---

        # Após consumir a cadeia (ou travar), verifica aceitação
        # É importante re-aplicar o fecho épsilon final, pois pode haver transições épsilon para estados finais
        estados_finais_alcancaveis = self.automato.fecho_epsilon(estados_atuais)
        aceita = any(self.automato.estados[e] in self.automato.estados_finais for e in estados_finais_alcancaveis if e in self.automato.estados)

        if aceita and indice_atual == len(self.cadeia_original): # Garante que toda a cadeia foi consumida
            yield {"status": "aceita", "mensagem": "Cadeia aceita!", "estado_atual": estados_finais_alcancaveis, "cadeia_restante": ""}
        elif not aceita and indice_atual == len(self.cadeia_original):
             yield {"status": "rejeita", "mensagem": "Cadeia consumida, mas nenhum estado final foi alcançado.", "estado_atual": estados_finais_alcancaveis, "cadeia_restante": ""}
        else: # Se indice_atual < len(cadeia_original), significa que travou antes
             yield {"status": "rejeita", "mensagem": f"Travou no processamento. Não foi possível consumir '{self.cadeia_original[indice_atual:]}'.", "estado_atual": estados_atuais, "cadeia_restante": self.cadeia_original[indice_atual:]}


# --- Simulador AP (Sem mudança significativa necessária para esta correção) ---
class SimuladorAP(SimuladorPassos):
    def _criar_gerador(self):
        # A lógica do AP já usa um índice (indice_cadeia) e pode potencialmente
        # lidar com s_in > 1 caractere se a chave de transição for criada assim.
        # A lógica de busca de 'possibilidades' pode precisar de ajuste se
        # s_in pode ter múltiplos caracteres, similar ao AFN/AFD com startswith.
        # Por enquanto, mantendo a lógica original que parece focar em um símbolo
        # de entrada ou epsilon por passo.

        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        # Inclui símbolo inicial Z se não for vazio
        pilha_inicial = [self.automato.simbolo_inicial_pilha] if self.automato.simbolo_inicial_pilha else []
        configs = [(self.automato.estado_inicial.nome, 0, pilha_inicial, None)] # (estado, indice_cadeia, pilha, transicao_anterior)
        visitados_ciclo = set() # (estado, indice_cadeia, tuple(pilha))
        max_steps = 1000 # Limite para evitar loops infinitos
        steps = 0

        while configs and steps < max_steps:
            estado_atual, indice_cadeia, pilha, transicao_anterior = configs.pop(0) # BFS para exploração ampla
            steps += 1

            # Evita revisitar a mesma configuração (estado, posição na cadeia, conteúdo da pilha)
            config_tupla = (estado_atual, indice_cadeia, tuple(pilha))
            if config_tupla in visitados_ciclo: continue
            visitados_ciclo.add(config_tupla)

            cadeia_restante = self.cadeia_original[indice_cadeia:]
            pilha_str = ''.join(pilha) if pilha else "(vazia)"

            yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "pilha": pilha_str, "transicao_ativa": transicao_anterior}

            # Verifica aceitação por estado final APÓS consumir toda a cadeia
            if indice_cadeia == len(self.cadeia_original):
                 # Considera fecho epsilon final para AP também? Opcional dependendo da definição.
                 # estados_finais_possiveis = self.automato.fecho_epsilon_ap({estado_atual}, pilha) # Função hipotética
                 if estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
                    yield {"status": "aceita", "mensagem": "Cadeia aceita por estado final!", "estado_atual": {estado_atual}, "pilha": pilha_str}; return
                 # Adicionar verificação de aceitação por pilha vazia se necessário aqui

            # Determina possíveis próximas transições
            simbolo_entrada_atual = self.cadeia_original[indice_cadeia] if indice_cadeia < len(self.cadeia_original) else EPSILON
            topo_pilha_atual = pilha[-1] if pilha else EPSILON

            possibilidades = [] # Lista de dicionários {'chave': (origem, s_in, s_pop), 'consome_entrada': bool, 'consome_pilha': bool}

            # 1. Transição com símbolo de entrada e símbolo da pilha
            if simbolo_entrada_atual != EPSILON and topo_pilha_atual != EPSILON:
                chave = (estado_atual, simbolo_entrada_atual, topo_pilha_atual)
                if chave in self.automato.transicoes:
                    possibilidades.append({'chave': chave, 'consome_entrada': True, 'consome_pilha': True})

            # 2. Transição com símbolo de entrada, sem consumir da pilha (epsilon no pop)
            if simbolo_entrada_atual != EPSILON:
                chave = (estado_atual, simbolo_entrada_atual, EPSILON)
                if chave in self.automato.transicoes:
                    possibilidades.append({'chave': chave, 'consome_entrada': True, 'consome_pilha': False})

            # 3. Transição epsilon na entrada, consumindo da pilha
            if topo_pilha_atual != EPSILON:
                chave = (estado_atual, EPSILON, topo_pilha_atual)
                if chave in self.automato.transicoes:
                    possibilidades.append({'chave': chave, 'consome_entrada': False, 'consome_pilha': True})

            # 4. Transição epsilon na entrada e epsilon na pilha
            chave = (estado_atual, EPSILON, EPSILON)
            if chave in self.automato.transicoes:
                 possibilidades.append({'chave': chave, 'consome_entrada': False, 'consome_pilha': False})


            # Explora cada possibilidade
            for p in possibilidades:
                chave_transicao = p['chave']
                destinos_e_push = self.automato.transicoes.get(chave_transicao, set()) # Pega o conjunto de (destino, s_push)

                for destino, simbolos_push in destinos_e_push:
                    nova_pilha = list(pilha) # Copia a pilha atual

                    # Desempilha se necessário
                    if p['consome_pilha']:
                        if not nova_pilha: continue # Não pode desempilhar de pilha vazia
                        nova_pilha.pop()

                    # Empilha se necessário (na ordem reversa)
                    if simbolos_push != EPSILON:
                        for char in reversed(simbolos_push):
                            nova_pilha.append(char)

                    # Avança na cadeia se necessário
                    novo_indice = indice_cadeia + 1 if p['consome_entrada'] else indice_cadeia

                    # Adiciona a nova configuração à fila, se não exceder limite
                    if steps < max_steps:
                        # Adiciona no INÍCIO da lista para DFS (pode explorar um caminho até o fim)
                        # ou no FIM para BFS (exploração em largura)
                        # Usando BFS (append) para garantir encontrar o caminho mais curto se houver.
                         configs.append((destino, novo_indice, nova_pilha, {(estado_atual, destino)}))

        # Se a fila esvaziou ou limite atingido, verifica se alguma config final levou à aceitação (já feito no loop)
        if steps >= max_steps:
            yield {"status": "rejeita", "mensagem": "Simulação interrompida (limite de passos atingido - possível loop infinito)."}
        else:
            # Se saiu do loop sem aceitar
             final_configs_check = [(s, idx, p) for s, idx, p, _ in configs if idx == len(self.cadeia_original)]
             aceitou_final = any(s in self.automato.estados and self.automato.estados[s] in self.automato.estados_finais for s, idx, p in final_configs_check)
             if not aceitou_final:
                 yield {"status": "rejeita", "mensagem": "Nenhum caminho levou a um estado de aceitação após consumir a cadeia."}
             # Se aceitou, o return dentro do loop já encerrou o gerador.


# --- NOVOS SIMULADORES (Moore e Mealy adaptados para múltiplos caracteres) ---

class SimuladorMoore(SimuladorPassos):
    def _criar_gerador(self):
        # Lógica adaptada similar ao AFD
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return
        if self.automato.estado_inicial.nome not in self.automato.estados:
             yield {"status": "erro", "mensagem": "Estado inicial não existe mais."}; return

        estado_atual = self.automato.estado_inicial.nome
        indice_atual = 0
        output_str = self.automato.estados[estado_atual].output or "" # Saída inicial

        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": self.cadeia_original[indice_atual:], "output": output_str, "transicao_ativa": set()}

        while indice_atual < len(self.cadeia_original):
            cadeia_restante_a_partir_do_indice = self.cadeia_original[indice_atual:]
            transicao_encontrada = None
            rotulo_consumido = ""
            proximo_estado = ""

            transicoes_possiveis = sorted(
                [(chave, destino) for chave, destino in self.automato.transicoes.items() if chave[0] == estado_atual],
                key=lambda item: len(item[0][1]), reverse=True
            )

            for (origem, rotulo), destino in transicoes_possiveis:
                if rotulo != EPSILON and cadeia_restante_a_partir_do_indice.startswith(rotulo):
                    transicao_encontrada = (origem, destino)
                    rotulo_consumido = rotulo
                    proximo_estado = destino
                    break

            if transicao_encontrada:
                estado_origem = estado_atual
                estado_atual = proximo_estado
                indice_atual += len(rotulo_consumido)
                cadeia_restante = self.cadeia_original[indice_atual:]
                # Adiciona a saída do *novo* estado
                output_str += self.automato.estados[estado_atual].output or ""
                
                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": {transicao_encontrada}}
            else:
                simbolo_atual_falha = self.cadeia_original[indice_atual] if indice_atual < len(self.cadeia_original) else "fim da cadeia"
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_origem}, começando com '{simbolo_atual_falha}').", "output": output_str, "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante_a_partir_do_indice}; return

        # Moore não "aceita" ou "rejeita", apenas finaliza
        yield {"status": "finalizado", "mensagem": "Cadeia processada.", "output": output_str, "estado_atual": {estado_atual}, "cadeia_restante": ""}


class SimuladorMealy(SimuladorPassos):
     def _criar_gerador(self):
        # Lógica adaptada similar ao AFD
        if not self.automato.estado_inicial:
            yield {"status": "erro", "mensagem": "Estado inicial não definido."}; return

        estado_atual = self.automato.estado_inicial.nome
        indice_atual = 0
        output_str = "" # Saída de Mealy começa vazia

        yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": self.cadeia_original[indice_atual:], "output": output_str, "transicao_ativa": set()}

        while indice_atual < len(self.cadeia_original):
            cadeia_restante_a_partir_do_indice = self.cadeia_original[indice_atual:]
            transicao_encontrada = None
            rotulo_consumido = ""
            proximo_estado = ""
            output_da_transicao = ""

            transicoes_possiveis = sorted(
                [(chave, destino_output) for chave, destino_output in self.automato.transicoes.items() if chave[0] == estado_atual],
                 key=lambda item: len(item[0][1]), reverse=True # Prioriza rótulos mais longos
            )

            for (origem, rotulo), (destino, output_t) in transicoes_possiveis:
                 if rotulo != EPSILON and cadeia_restante_a_partir_do_indice.startswith(rotulo):
                    transicao_encontrada = (origem, destino)
                    rotulo_consumido = rotulo
                    proximo_estado = destino
                    output_da_transicao = output_t or ""
                    break

            if transicao_encontrada:
                estado_origem = estado_atual
                estado_atual = proximo_estado
                indice_atual += len(rotulo_consumido)
                cadeia_restante = self.cadeia_original[indice_atual:]
                # Adiciona a saída da *transição*
                output_str += output_da_transicao
                
                yield {"status": "executando", "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante, "output": output_str, "transicao_ativa": {transicao_encontrada}}
            else:
                simbolo_atual_falha = self.cadeia_original[indice_atual] if indice_atual < len(self.cadeia_original) else "fim da cadeia"
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_origem}, começando com '{simbolo_atual_falha}').", "output": output_str, "estado_atual": {estado_atual}, "cadeia_restante": cadeia_restante_a_partir_do_indice}; return

        yield {"status": "finalizado", "mensagem": "Cadeia processada.", "output": output_str, "estado_atual": {estado_atual}, "cadeia_restante": ""}

# --- Simulador MT (Não precisa de mudança para esta correção específica) ---
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
        # A lógica da MT já opera sobre um único símbolo lido da fita (fita[cabecote])
        # por passo, então não precisa da lógica startswith baseada na cadeia original.
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
            
            # Checa se parou em estado final
            if estado_atual in self.automato.estados and self.automato.estados[estado_atual] in self.automato.estados_finais:
                yield {"status": "aceita", "mensagem": "Cadeia aceita!", "estado_atual": {estado_atual}, "tape": fita_str, "transicao_ativa": set()}; return

            simbolo_lido = fita[cabecote]
            chave_transicao = (estado_atual, simbolo_lido)

            # Estado atual antes da transição
            yield {"status": "executando", "estado_atual": {estado_atual}, "tape": fita_str, "transicao_ativa": set()} 

            if chave_transicao not in self.automato.transicoes:
                yield {"status": "rejeita", "mensagem": f"Transição indefinida para ({estado_atual}, {simbolo_lido}).", "estado_atual": {estado_atual}, "tape": fita_str}; return

            # Executa a transição
            estado_origem = estado_atual
            (prox_estado, simbolo_escrito, direcao) = self.automato.transicoes[chave_transicao]
            
            fita[cabecote] = simbolo_escrito # Escreve na fita
            
            # Move o cabeçote
            if direcao == 'R':
                cabecote += 1
            elif direcao == 'L':
                cabecote -= 1
                
            estado_atual = prox_estado # Muda para o próximo estado
            
            # Yield extra opcional para mostrar o estado *depois* da transição e movimento
            # fita_str_apos = self._visualizar_fita(fita, cabecote)
            # yield {"status": "executando", "estado_atual": {estado_atual}, "tape": fita_str_apos, "transicao_ativa": {(estado_origem, estado_atual)}}


        if steps >= max_steps:
            fita_str_final = self._visualizar_fita(fita, cabecote)
            yield {"status": "rejeita", "mensagem": "Simulação interrompida (limite de passos atingido).", "estado_atual": {estado_atual}, "tape": fita_str_final}