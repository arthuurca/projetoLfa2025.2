import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog # Adicionado filedialog
import math
import os # Adicionado os
import xml.etree.ElementTree as ET # Adicionado ET para JFF
from xml.dom import minidom # Adicionado minidom para JFF
from PIL import ImageGrab, Image # Adicionado ImageGrab e Image para JPG

from automato.automato_finito import AFD, AFN
from automato.automato_pilha import AutomatoPilha
from automato.maquinas_moore_mealy import MaquinaMoore, MaquinaMealy
from automato.maquina_turing import MaquinaTuring
from automato import EPSILON
from simulador.simulador_passos import (
    SimuladorAFD, SimuladorAFN, SimuladorAP,
    SimuladorMoore, SimuladorMealy, SimuladorMT
)
from collections import defaultdict

STATE_RADIUS = 25
FONT = ("Segoe UI", 10)

class TelaPrincipal:
    """Classe principal que gerencia a interface gráfica do simulador."""
    def __init__(self, master, voltar_menu_callback=None):
        """Inicializa a tela principal, configurando widgets e layout."""
        self.master = master
        self.voltar_menu_callback = voltar_menu_callback
        self.master.title("Simulador de Autômatos Visual")
        master.geometry("1200x800")

        self.automato = None
        self.tipo_automato = tk.StringVar(value="AFD")
        self.contador_estados = 0
        self.positions = {}
        self.label_hitboxes = {}

        # --- Cores e Estilos ---
        self.default_fg_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        self.active_button_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        self.cor_consumida = "#1f9223"
        self.cor_aceita = "#1f9223"
        self.cor_rejeita = "#ff6666"
        self.cor_finalizado = "#007acc" # Azul para Moore/Mealy
        self.canvas_bg = "#FFFFFF"
        self.canvas_fg_color = "black"
        self.canvas_estado_fill = "white"
        self.canvas_estado_text = "black"
        self.canvas_transicao_text = "blue"
        self.canvas_transicao_ativa = "#1f9223"
        self.canvas_estado_ativo = "#ff6666"

        # --- NOVAS CORES SEMÂNTICAS ---
        self.cor_destrutiva_fg = "#d32f2f"
        self.cor_destrutiva_hover = "#b71c1c"
        self.cor_navegacao_fg = "#565b5e"
        self.cor_navegacao_hover = "#4a4f52"
        self.cor_ferramenta_fg = "#6c757d"    # Cinza médio
        self.cor_ferramenta_hover = "#5a6268" # Cinza médio mais escuro

        # --- ESTILO PADRÃO PARA BOTÕES E WIDGETS ---
        self.style_font_bold = ctk.CTkFont(size=12, weight="bold")

        self.style_top_widget = {
            "corner_radius": 10
        }
        self.style_tool_button = {
            "corner_radius": 10,
            "font": self.style_font_bold,
            "border_spacing": 5
        }
        self.style_sim_button = {
            "corner_radius": 10,
            "font": self.style_font_bold
        }
        self.style_dialog_widget = {
            "corner_radius": 10
        }

        # --- Variáveis de Estado da UI ---
        self.current_mode = "MOVER"
        self.tool_buttons = {}
        self.origem_transicao = None
        self.estado_movendo = None
        self.simulador = None

        # --- Layout Principal ---
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(2, weight=1)
        self.master.grid_rowconfigure(3, weight=0)
        self.master.grid_rowconfigure(4, weight=0)

        # --- 1. Barra Superior ---
        top_bar = ctk.CTkFrame(master)
        top_bar.grid(row=0, column=0, padx=10, pady=(10,5), sticky="new")

        ctk.CTkLabel(top_bar, text="Tipo de Autômato:").pack(side="left", padx=(10,5))
        tipos_maquina = ["AFD", "AFN", "AP", "Moore", "Mealy", "Turing"]
        tipo_menu = ctk.CTkComboBox(top_bar, variable=self.tipo_automato,
                                      values=tipos_maquina, command=self.mudar_tipo_automato,
                                      **self.style_top_widget)
        tipo_menu.pack(side="left", padx=5)

        self.btn_limpar = ctk.CTkButton(top_bar,
                                        text="💀 Limpar Tudo",
                                        command=self.limpar_tela,
                                        width=100,
                                        fg_color=self.cor_destrutiva_fg,
                                        hover_color=self.cor_destrutiva_hover,
                                        **self.style_top_widget
                                        )
        self.btn_limpar.pack(side="left", padx=(20, 10))

        self.btn_theme_toggle = ctk.CTkButton(top_bar, text="",
                                              command=self.toggle_theme, width=120,
                                              **self.style_top_widget)
        self.btn_theme_toggle.pack(side="left", padx=10)
        self.update_theme_button_text()

        self.btn_export_jff = ctk.CTkButton(top_bar, text="💾 Salvar JFF",
                                            command=self.exportar_para_jff, width=120,
                                            fg_color=self.cor_ferramenta_fg,
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_export_jff.pack(side="left", padx=(20, 5))

        self.btn_export_jpg = ctk.CTkButton(top_bar, text="🖼️ Salvar JPG",
                                            command=self.exportar_para_jpg, width=120,
                                            fg_color=self.cor_ferramenta_fg,
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_export_jpg.pack(side="left", padx=5)


        if self.voltar_menu_callback:
            self.btn_voltar = ctk.CTkButton(
            top_bar,
            text="← Voltar ao Menu",
            command=self.voltar_ao_menu,
            width=140,
            fg_color=self.cor_navegacao_fg,
            hover_color=self.cor_navegacao_hover,
            **self.style_top_widget
        )
        self.btn_voltar.pack(side="right", padx=(10, 10))

        # --- 2. Barra de Ferramentas ---

        tool_bar_container = ctk.CTkFrame(master, fg_color="transparent")
        tool_bar_container.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        tool_bar = ctk.CTkFrame(tool_bar_container)
        tool_bar.pack(anchor="center")

        btn_inicial = ctk.CTkButton(tool_bar, text="► Inicial", command=lambda mid="INICIAL": self.set_active_mode(mid), fg_color=self.cor_ferramenta_fg, hover_color=self.cor_ferramenta_hover, **self.style_tool_button)
        btn_inicial.pack(side="left", padx=5, pady=5); self.tool_buttons["INICIAL"] = btn_inicial
        btn_final = ctk.CTkButton(tool_bar, text="◎ Final", command=lambda mid="FINAL": self.set_active_mode(mid), fg_color=self.cor_ferramenta_fg, hover_color=self.cor_ferramenta_hover, **self.style_tool_button)
        btn_final.pack(side="left", padx=5, pady=5); self.tool_buttons["FINAL"] = btn_final
        btn_estado = ctk.CTkButton(tool_bar, text="○ Estado", command=lambda mid="ESTADO": self.set_active_mode(mid), fg_color=self.cor_ferramenta_fg, hover_color=self.cor_ferramenta_hover, **self.style_tool_button)
        btn_estado.pack(side="left", padx=5, pady=5); self.tool_buttons["ESTADO"] = btn_estado
        btn_deletar = ctk.CTkButton(tool_bar, text="❌ Deletar", command=lambda mid="DELETAR": self.set_active_mode(mid), fg_color=self.cor_destrutiva_fg, hover_color=self.cor_destrutiva_hover, **self.style_tool_button)
        btn_deletar.pack(side="left", padx=5, pady=5); self.tool_buttons["DELETAR"] = btn_deletar
        btn_mover = ctk.CTkButton(tool_bar, text="✥ Mover/Editar", command=lambda mid="MOVER": self.set_active_mode(mid), fg_color=self.cor_ferramenta_fg, hover_color=self.cor_ferramenta_hover, **self.style_tool_button)
        btn_mover.pack(side="left", padx=5, pady=5); self.tool_buttons["MOVER"] = btn_mover
        btn_transicao = ctk.CTkButton(tool_bar, text="→ Transição", command=lambda mid="TRANSICAO": self.set_active_mode(mid), fg_color=self.cor_ferramenta_fg, hover_color=self.cor_ferramenta_hover, **self.style_tool_button)
        btn_transicao.pack(side="left", padx=5, pady=5); self.tool_buttons["TRANSICAO"] = btn_transicao


        # --- 3. Canvas ---
        self.canvas = tk.Canvas(master, bg=self.canvas_bg, bd=0, highlightthickness=0)
        self.canvas.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # --- 4. Frame Fita/Saída ---
        self.frame_extra_info = ctk.CTkFrame(master)
        self.frame_extra_info.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.frame_extra_info.grid_columnconfigure(1, weight=1)

        self.lbl_output_tag = ctk.CTkLabel(self.frame_extra_info, text="Saída:", font=ctk.CTkFont(weight="bold"))
        self.lbl_output_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.cor_finalizado)

        self.lbl_tape_tag = ctk.CTkLabel(self.frame_extra_info, text="Fita:", font=ctk.CTkFont(weight="bold"))
        self.lbl_tape_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(family="Courier New", size=16, weight="bold"))

        # --- 5. Barra Inferior (Simulação) ---
        frame_simulacao = ctk.CTkFrame(master)
        frame_simulacao.grid(row=4, column=0, padx=10, pady=(5,10), sticky="sew")
        frame_simulacao.grid_columnconfigure(1, weight=1)
        frame_simulacao.grid_columnconfigure(4, weight=1)
        frame_simulacao.grid_columnconfigure(5, weight=0)

        ctk.CTkLabel(frame_simulacao, text="Entrada:").grid(row=0, column=0, padx=(10,5), pady=10)
        self.entrada_cadeia = ctk.CTkEntry(frame_simulacao,
                                           placeholder_text="Digite a cadeia para simular...",
                                           **self.style_top_widget)
        self.entrada_cadeia.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.btn_simular = ctk.CTkButton(frame_simulacao, text="▶ Iniciar",
                                         command=self.iniciar_simulacao, width=100,
                                         fg_color=self.cor_ferramenta_fg,
                                         hover_color=self.cor_ferramenta_hover,
                                         **self.style_sim_button)
        self.btn_simular.grid(row=0, column=2, padx=5, pady=10)

        self.btn_proximo_passo = ctk.CTkButton(frame_simulacao, text="Passo >",
                                               command=self.executar_proximo_passo, width=100,
                                               fg_color=self.cor_ferramenta_fg,
                                               hover_color=self.cor_ferramenta_hover,
                                               **self.style_sim_button)
        self.btn_proximo_passo.grid(row=0, column=3, padx=5, pady=10)

        cadeia_status_frame = ctk.CTkFrame(frame_simulacao, fg_color="transparent")
        cadeia_status_frame.grid(row=0, column=4, padx=10, pady=10, sticky="w")

        # --- ATUALIZAÇÃO: Tamanho da fonte aumentado para 22 ---
        self.lbl_cadeia_consumida = ctk.CTkLabel(cadeia_status_frame, text="", text_color=self.cor_consumida, font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_cadeia_consumida.pack(side="left")
        self.lbl_cadeia_restante = ctk.CTkLabel(cadeia_status_frame, text="", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_cadeia_restante.pack(side="left")

        # --- ATUALIZAÇÃO: Tamanho da fonte aumentado para 14 ---
        self.lbl_status_simulacao = ctk.CTkLabel(frame_simulacao, text="Status: Aguardando", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_status_simulacao.grid(row=0, column=5, padx=10, pady=10, sticky="e")
        # --- FIM DAS ATUALIZAÇÕES ---


        # --- Bindings e Inicialização ---
        self.canvas.bind("<Button-1>", self.clique_canvas)
        self.canvas.bind("<Double-Button-1>", self.duplo_clique_canvas)
        self.canvas.bind("<B1-Motion>", self.arrastar_canvas)
        self.canvas.bind("<ButtonRelease-1>", self.soltar_canvas)

        self.mudar_tipo_automato()
        self.set_active_mode("MOVER")
        self.btn_proximo_passo.configure(state="disabled")
        self._atualizar_widgets_extra_info()

    # --- FUNÇÕES DE CONTROLE DE MODO ---
    def set_active_mode(self, mode_id):
        """Define o modo de interação atual (criar estado, transição, mover, etc.)."""
        if mode_id == self.current_mode: self.current_mode = "MOVER" # Desativa ao clicar novamente
        else: self.current_mode = mode_id
        self.update_button_styles()
        self.update_cursor_and_status()

    def update_button_styles(self):
        """Atualiza a cor dos botões da barra de ferramentas para indicar o modo ativo."""
        for mode_id, button in self.tool_buttons.items():
            is_active = (mode_id == self.current_mode)

            # Define cores diferentes para o botão de deletar
            if mode_id == "DELETAR":
                color = self.cor_destrutiva_hover if is_active else self.cor_destrutiva_fg
                button.configure(fg_color=color)
            else:
                color = self.cor_ferramenta_hover if is_active else self.cor_ferramenta_fg
                button.configure(fg_color=color)

    def update_cursor_and_status(self):
        """Muda o cursor do mouse de acordo com o modo ativo e reseta a origem da transição."""
        mode = self.current_mode
        # Mapeia cada modo para um estilo de cursor
        cursor_map = { "ESTADO": "crosshair", "TRANSICAO": "hand2", "INICIAL": "arrow",
                       "FINAL": "star", "MOVER": "fleur", "DELETAR": "X_cursor" }
        self.master.config(cursor=cursor_map.get(mode, "arrow")) # Usa 'arrow' como padrão
        self.origem_transicao = None # Limpa a seleção de origem ao mudar de modo


    # --- FUNÇÕES DE TEMA ---
    def toggle_theme(self):
        """Alterna entre o tema claro e escuro."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

        self.update_theme_button_text() # Atualiza o texto do botão de tema

        # Atualiza cores dependentes do tema e redesenha
        self.default_fg_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        self.update_button_styles()
        self.desenhar_automato()

    def voltar_ao_menu(self):
        """Retorna para a tela de menu inicial, destruindo a tela atual."""
        if self.voltar_menu_callback:
            if self.simulador:
                self.parar_simulacao() # Para a simulação se estiver ativa
            # Destroi todos os widgets da tela principal
            for widget in self.master.winfo_children():
                widget.destroy()
            self.voltar_menu_callback() # Chama a função que recria o menu

    def update_theme_button_text(self):
        """Atualiza o texto e as cores do botão de alternar tema."""
        current_mode = ctk.get_appearance_mode()

        # Define texto e cores com base no tema atual
        if current_mode == "Dark":
            button_text = "☀️Modo Claro"
            btn_fg_color = "#F0F0F0"
            btn_hover_color = "#D5D5D5"
            btn_text_color = "#1A1A1A"
        else:
            button_text = "🌙Modo Escuro"
            btn_fg_color = "#333333"
            btn_hover_color = "#4A4A4A"
            btn_text_color = "#E0E0E0"

        # Aplica as configurações ao botão
        self.btn_theme_toggle.configure(
            text=button_text,
            fg_color=btn_fg_color,
            hover_color=btn_hover_color,
            text_color=btn_text_color
        )


    # --- FUNÇÕES DE UI ---
    def _atualizar_widgets_extra_info(self):
        """Mostra ou esconde os labels de 'Saída' ou 'Fita' dependendo do tipo de autômato."""
        tipo = self.tipo_automato.get()
        # Esconde todos primeiro
        self.lbl_output_tag.grid_remove()
        self.lbl_output_valor.grid_remove()
        self.lbl_tape_tag.grid_remove()
        self.lbl_tape_valor.grid_remove()

        # Mostra o label de Saída para Moore ou Mealy
        if tipo in ["Moore", "Mealy"]:
            self.lbl_output_tag.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
            self.lbl_output_valor.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # Mostra o label de Fita para Turing
        elif tipo == "Turing":
            self.lbl_tape_tag.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
            self.lbl_tape_valor.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Esconde o frame inteiro se não for Moore, Mealy ou Turing
        if tipo in ["AFD", "AFN", "AP"]:
             self.frame_extra_info.grid_remove()
        else:
             self.frame_extra_info.grid() # Mostra o frame se for necessário

    def mudar_tipo_automato(self, event=None):
        """Chamado quando o tipo de autômato é alterado no ComboBox."""
        self.limpar_tela() # Reseta a tela
        self._atualizar_widgets_extra_info() # Atualiza os widgets extras

    def limpar_tela(self):
        """Reseta o autômato, posições e estado da simulação."""
        self.contador_estados = 0
        tipo = self.tipo_automato.get()
        # Cria uma nova instância do autômato correspondente
        if tipo == "AFD": self.automato = AFD()
        elif tipo == "AFN": self.automato = AFN()
        elif tipo == "AP": self.automato = AutomatoPilha()
        elif tipo == "Moore": self.automato = MaquinaMoore()
        elif tipo == "Mealy": self.automato = MaquinaMealy()
        elif tipo == "Turing": self.automato = MaquinaTuring()

        self.positions = {} # Limpa posições dos estados
        self.parar_simulacao(final_state=False) # Para e reseta a simulação
        self.set_active_mode("MOVER") # Volta para o modo padrão
        self.desenhar_automato() # Limpa e redesenha o canvas
        self._atualizar_widgets_extra_info() # Atualiza widgets extras


    # --- AÇÕES DO CANVAS ---
    def clique_canvas(self, event):
        """Processa um clique no canvas de acordo com o modo ativo."""
        mode = self.current_mode
        estado_clicado = self._get_estado_em(event.x, event.y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y)

        # Se modo ESTADO e clicou em espaço vazio: cria novo estado
        if mode == "ESTADO" and not estado_clicado and not transicao_clicada:
            nome_estado = f"q{self.contador_estados}"
            # Garante nome único
            while nome_estado in self.automato.estados:
                self.contador_estados += 1; nome_estado = f"q{self.contador_estados}"

            # Se for Moore, pede o output
            if self.tipo_automato.get() == "Moore":
                dialog = ctk.CTkInputDialog(text="Símbolo de Saída do Estado (vazio=default):", title="Criar Estado Moore")
                output = dialog.get_input()
                if output is None: return # Cancelou
                self.automato.adicionar_estado(nome_estado, event.x, event.y, output=output)
            else:
                self.automato.adicionar_estado(nome_estado, event.x, event.y)

            self.positions[nome_estado] = (event.x, event.y)
            self.contador_estados += 1
        # Se clicou em um estado: processa de acordo com o modo
        elif estado_clicado:
            if mode == "TRANSICAO": # Define origem ou cria transição
                if not self.origem_transicao:
                    self.origem_transicao = estado_clicado # Primeiro clique define origem
                else:
                    self._criar_transicao(self.origem_transicao, estado_clicado) # Segundo clique cria
                    self.origem_transicao = None
            elif mode == "INICIAL": self.automato.definir_estado_inicial(estado_clicado.nome)
            elif mode == "FINAL": self.automato.alternar_estado_final(estado_clicado.nome)
            elif mode == "MOVER": self.estado_movendo = estado_clicado # Prepara para arrastar
            elif mode == "DELETAR": # Deleta o estado
                nome_a_deletar = estado_clicado.nome
                self.automato.deletar_estado(nome_a_deletar)
                self.positions.pop(nome_a_deletar, None) # Remove da lista de posições
            else: pass # Outros modos não fazem nada ao clicar no estado
        # Se clicou numa label de transição no modo DELETAR: deleta a transição
        elif transicao_clicada and mode == "DELETAR":
            origem, destino = transicao_clicada
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            else: # Fallback caso o método não exista no tipo de automato
                print(f"Aviso: Método 'deletar_transicoes_entre' não implementado para {type(self.automato)}")
        # Se clicou em espaço vazio (e não está no modo ESTADO): cancela criação de transição
        elif not estado_clicado and not transicao_clicada:
            self.origem_transicao = None

        self.desenhar_automato() # Redesenha o autômato após qualquer ação

    def duplo_clique_canvas(self, event):
        """Processa um duplo clique no canvas (renomear estado ou editar transição no modo MOVER)."""
        mode = self.current_mode
        estado_clicado = self._get_estado_em(event.x, event.y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y)

        # Se deu duplo clique num estado no modo MOVER: renomeia (e edita output se for Moore)
        if estado_clicado and mode == "MOVER":
            novo_nome = ctk.CTkInputDialog(text="Digite o novo nome do estado:", title="Renomear Estado").get_input()

            # Se for Moore, pede também o novo output
            if self.tipo_automato.get() == "Moore":
                novo_output = ctk.CTkInputDialog(text="Digite a nova saída do estado:", title="Editar Saída Moore").get_input()
                if novo_output is not None: # Permite cancelar
                    self.automato.set_output_estado(estado_clicado.nome, novo_output)

            # Se um novo nome foi digitado e é diferente do antigo
            if novo_nome and novo_nome != estado_clicado.nome:
                try:
                    pos = self.positions.pop(estado_clicado.nome) # Salva posição
                    self.automato.renomear_estado(estado_clicado.nome, novo_nome)
                    self.positions[novo_nome] = pos # Atualiza posição com novo nome
                except ValueError as e: # Se o nome já existir
                    messagebox.showerror("Erro ao Renomear", str(e))
                    # Restaura a posição se o nome antigo ainda existir (caso de erro)
                    if estado_clicado.nome in self.automato.estados: self.positions[estado_clicado.nome] = pos
            self.desenhar_automato()
        # Se deu duplo clique numa label de transição no modo MOVER: edita a transição
        elif transicao_clicada and mode == "MOVER":
            origem, destino = transicao_clicada
            self._editar_label_transicao(origem, destino)

    def _editar_label_transicao(self, origem, destino):
        """Abre um diálogo para editar os símbolos de uma transição (exceto AP, Mealy, Turing)."""
        tipo = self.tipo_automato.get()
        # Edição por duplo clique não implementada para tipos complexos
        if tipo in ["AP", "Mealy", "Turing"]:
            messagebox.showinfo("Editar Transição", f"Edição de transições {tipo} não implementada com duplo clique. Use Deletar e Criar.", parent=self.master)
            return

        # Pega os símbolos atuais da transição
        simbolos_atuais = set()
        agrupado = self._agrupar_transicoes()
        if origem in agrupado and destino in agrupado[origem]:
            simbolos_atuais = agrupado[origem][destino]

        # Formata para exibição no diálogo ('e' para epsilon)
        label_atual = ",".join(sorted(list(s.replace(EPSILON, "e") for s in simbolos_atuais)))

        # Abre diálogo preenchido com os símbolos atuais
        dialog = ctk.CTkInputDialog(text="Símbolo(s) (use 'e' para ε, vírgula para separar):", title="Editar Transição")
        dialog.entry.insert(0, label_atual)
        simbolo_input = dialog.get_input()

        # Se o usuário confirmou
        if simbolo_input is not None:
            # Deleta as transições antigas entre esses estados
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            # Adiciona as novas transições
            novos_simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
            for s in novos_simbolos:
                simbolo_final = EPSILON if s == 'e' else s # Converte 'e' de volta para epsilon
                self.automato.adicionar_transicao(origem, simbolo_final, destino)
            self.desenhar_automato()


    def _criar_transicao(self, origem, destino):
        """Abre o diálogo apropriado para criar uma transição entre dois estados."""
        tipo = self.tipo_automato.get()

        # Diálogo simples para AFD, AFN, Moore
        if tipo in ["AFD", "AFN", "Moore"]:
            dialog = ctk.CTkInputDialog(text="Símbolo(s) (use 'e' para ε, vírgula para separar):", title=f"Criar Transição {tipo}")
            simbolo_input = dialog.get_input()
            if simbolo_input is not None:
                simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
                for s in simbolos:
                    simbolo_final = EPSILON if s == 'e' else s
                    self.automato.adicionar_transicao(origem.nome, simbolo_final, destino.nome)

        # Diálogo específico para AP
        elif tipo == "AP":
            dlg = TransicaoPilhaDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg) # Espera o diálogo fechar
            if dlg.resultado: # Se não foi cancelado
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['entrada'], dlg.resultado['pop'], destino.nome, dlg.resultado['push'])

        # Diálogo específico para Mealy
        elif tipo == "Mealy":
            dlg = TransicaoMealyDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                simbolo = EPSILON if dlg.resultado['simbolo'] == 'e' else dlg.resultado['simbolo']
                output = EPSILON if dlg.resultado['output'] == 'e' else dlg.resultado['output']
                self.automato.adicionar_transicao(origem.nome, simbolo, destino.nome, output)

        # Diálogo específico para Turing
        elif tipo == "Turing":
            dlg = TransicaoTuringDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['lido'], destino.nome, dlg.resultado['escrito'], dlg.resultado['dir'])

        self.desenhar_automato() # Redesenha após criar


    def arrastar_canvas(self, event):
        """Move o estado selecionado enquanto o mouse é arrastado."""
        if self.estado_movendo and self.estado_movendo.nome in self.positions:
            self.positions[self.estado_movendo.nome] = (event.x, event.y)
            self.desenhar_automato() # Redesenha a cada movimento
    def soltar_canvas(self, event):
        """Finaliza o arraste do estado."""
        self.estado_movendo = None

    def _get_estado_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão dentro de algum estado desenhado."""
        for nome, (sx, sy) in self.positions.items():
            # Calcula a distância do clique ao centro do estado
            if (sx - x)**2 + (sy - y)**2 <= (STATE_RADIUS + 2)**2: # Usa raio com margem
                if nome in self.automato.estados: return self.automato.estados[nome]
        return None

    def _get_transicao_label_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão sobre alguma label de transição."""
        # Pega todos os itens do canvas na área do clique
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        # Itera de trás para frente (itens desenhados por último ficam na frente)
        for item_id in reversed(items):
            tags = self.canvas.gettags(item_id)
            # Se o item tem a tag 'transition_label'
            if "transition_label" in tags:
                # Procura por uma tag no formato 'label_origem_destino'
                for tag in tags:
                    if tag.startswith("label_"):
                        parts = tag.split('_')
                        if len(parts) == 3: return parts[1], parts[2] # Retorna (origem, destino)
        return None

    # --- FUNÇÕES DE DESENHO ---
    def desenhar_automato(self, estados_ativos=None, transicoes_ativas=None, extra_info_str=None):
            """Desenha o autômato completo no canvas, destacando estados/transições ativas."""
            try:
                self.canvas.delete("all") # Limpa o canvas
                self.label_hitboxes.clear() # Limpa áreas clicáveis das labels
                transicoes_ativas = transicoes_ativas or set()
                agrupado = self._agrupar_transicoes() # Agrupa transições com formato JFLAP
                pares_processados = set() # Para evitar desenhar transições duplas duas vezes
                tipo = self.tipo_automato.get()

                # --- DESENHAR TRANSIÇÕES ---
                for origem_nome, destino_info in agrupado.items():
                    if origem_nome not in self.automato.estados or origem_nome not in self.positions: continue
                    origem = self.automato.estados[origem_nome]
                    x1, y1 = self.positions[origem_nome]

                    for destino_nome, simbolos in destino_info.items():
                        if destino_nome not in self.automato.estados or destino_nome not in self.positions: continue
                        destino = self.automato.estados[destino_nome]
                        x2, y2 = self.positions[destino_nome]
                        par = tuple(sorted((origem_nome, destino_nome))) # Identificador único do par

                        # Define cor e largura da linha (destaca se ativa)
                        cor_linha = self.canvas_transicao_ativa if (origem_nome, destino_nome) in transicoes_ativas else self.canvas_fg_color
                        largura = 2.5 if cor_linha == self.canvas_transicao_ativa else 1.5
                        # Cria a label para exibição (símbolos JFLAP empilhados)
                        label_exibicao = "\n".join(sorted(list(simbolos))) # Usa os símbolos já formatados
                        label_tag = f"label_{origem_nome}_{destino_nome}" # Tag para identificar a label

                        # Define a fonte padrão para transições (preto, negrito)
                        transicao_font = (FONT[0], FONT[1], "bold")
                        transicao_color = self.canvas_fg_color # Preto

                        if origem_nome == destino_nome: # Loop (transição para o próprio estado)
                            # Desenha o texto da transição ACIMA do arco
                            text_id = self.canvas.create_text(
                                x1, y1 - 75, # Posição Y ajustada
                                text=label_exibicao,
                                fill=transicao_color, # Cor preta
                                font=transicao_font,  # Fonte negrito
                                anchor=tk.CENTER,
                                tags=("transition_label_text", label_tag)
                            )
                            # Desenha o arco do loop
                            p1_x, p1_y = x1 - 10, y1 - STATE_RADIUS
                            c1_x, c1_y = x1 - 40, y1 - (STATE_RADIUS + 35)
                            c2_x, c2_y = x1 + 40, y1 - (STATE_RADIUS + 35)
                            p2_x, p2_y = x1 + 10, y1 - STATE_RADIUS
                            self.canvas.create_line(p1_x, p1_y, c1_x, c1_y, c2_x, c2_y, p2_x, p2_y,
                                                    smooth=True, arrow=tk.LAST,
                                                    fill=cor_linha, width=largura, tags="linha_transicao")
                            # Armazena a área da label
                            bbox = self.canvas.bbox(text_id)
                            if bbox: self.label_hitboxes[label_tag] = bbox

                        elif agrupado.get(destino_nome, {}).get(origem_nome): # Transição dupla
                            if par in pares_processados: continue
                            cor_linha_volta = self.canvas_transicao_ativa if (destino_nome, origem_nome) in transicoes_ativas else self.canvas_fg_color
                            largura_volta = 2.5 if cor_linha_volta == self.canvas_transicao_ativa else 1.5
                            label_tag_volta = f"label_{destino_nome}_{origem_nome}"
                            label_volta_interna = ",".join(sorted(list(agrupado[destino_nome][origem_nome]))) # Usa vírgula para passar para _desenhar_linha_curva
                            label_ida_interna = ",".join(sorted(list(simbolos))) # Usa vírgula para passar para _desenhar_linha_curva
                            # Desenha as duas linhas curvas
                            self._desenhar_linha_curva(origem, destino, label_ida_interna, 30, cor_linha, largura, label_tag)
                            self._desenhar_linha_curva(destino, origem, label_volta_interna, 30, cor_linha_volta, largura_volta, label_tag_volta)
                            pares_processados.add(par)
                        else: # Transição reta simples
                            dx, dy = x2 - x1, y2 - y1
                            dist = math.hypot(dx, dy) or 1
                            ux, uy = dx/dist, dy/dist
                            start_x, start_y = x1 + ux * STATE_RADIUS, y1 + uy * STATE_RADIUS
                            end_x, end_y = x2 - ux * STATE_RADIUS, y2 - uy * STATE_RADIUS
                            # Desenha a linha reta
                            self.canvas.create_line(start_x, start_y, end_x, end_y,
                                                    arrow=tk.LAST,
                                                    fill=cor_linha, width=largura, tags="linha_transicao")
                            # Posição da label
                            text_x = (start_x+end_x)/2 - uy*15
                            text_y = (start_y+end_y)/2 + ux*15
                            # Desenha a label empilhada
                            text_id = self.canvas.create_text(
                                text_x, text_y,
                                text=label_exibicao,
                                fill=transicao_color, # Cor preta
                                font=transicao_font,  # Fonte negrito
                                anchor=tk.CENTER,
                                tags=("transition_label_text", label_tag)
                            )
                            bbox = self.canvas.bbox(text_id)
                            if bbox: self.label_hitboxes[label_tag] = bbox

                # --- DESENHAR ESTADOS ---
                for nome, estado in self.automato.estados.items():
                    if nome not in self.positions: continue
                    x, y = self.positions[nome]
                    cor_borda = self.canvas_estado_ativo if estados_ativos and nome in estados_ativos else self.canvas_fg_color
                    self.canvas.create_oval(x - STATE_RADIUS, y - STATE_RADIUS, x + STATE_RADIUS, y + STATE_RADIUS,
                                            fill=self.canvas_estado_fill, outline=cor_borda,
                                            width=3 if cor_borda == self.canvas_estado_ativo else 2,
                                            tags=("estado_circulo", f"estado_{nome}"))

                    texto_estado = nome
                    if tipo == "Moore" and estado.output:
                        texto_estado = f"{nome}\n({estado.output})"
                    self.canvas.create_text(x, y, text=texto_estado, font=FONT,
                                            fill=self.canvas_estado_text, justify=tk.CENTER,
                                            tags=("estado_texto", f"estado_{nome}_texto"))

                    if estado.is_final:
                        self.canvas.create_oval(x - (STATE_RADIUS - 5), y - (STATE_RADIUS - 5),
                                                x + (STATE_RADIUS - 5), y + (STATE_RADIUS - 5),
                                                outline=cor_borda, width=1,
                                                tags=("estado_final_circulo", f"estado_{nome}"))
                    if estado.is_inicial:
                        self.canvas.create_line(x - STATE_RADIUS - 20, y, x - STATE_RADIUS, y,
                                                arrow=tk.LAST,
                                                width=2, fill=self.canvas_fg_color,
                                                tags=("estado_inicial_seta", f"estado_{nome}"))

                # --- OUTROS ELEMENTOS ---
                if self.origem_transicao and self.origem_transicao.nome in self.positions:
                    x, y = self.positions[self.origem_transicao.nome]
                    self.canvas.create_oval(x-STATE_RADIUS-3, y-STATE_RADIUS-3, x+STATE_RADIUS+3, y+STATE_RADIUS+3,
                                            outline="#33cc33", width=2, dash=(4, 4),
                                            tags="origem_transicao_destaque")

                if extra_info_str is not None:
                    tag = "Pilha: " if tipo == "AP" else ("Fita: " if tipo == "Turing" else "")
                    if tag:
                        bg_rect = self.canvas.create_rectangle(10, 10, 10 + len(tag + extra_info_str) * 8 + 10, 40,
                                                            fill="#f0f0f0", outline="", tags="extra_info_bg")
                        info_text = self.canvas.create_text(15, 25, text=f"{tag}{extra_info_str}", font=FONT,
                                                            fill=self.canvas_fg_color, anchor="w", tags="extra_info_text")
                        text_bbox = self.canvas.bbox(info_text)
                        if text_bbox:
                            self.canvas.coords(bg_rect, 10, 10, text_bbox[2] + 5, 40)

            except Exception as e:
                print(f"Erro crítico ao desenhar automato: {e}")

    def _desenhar_linha_curva(self, origem, destino, label_original_virgula, fator, cor_linha, largura, label_tag):
            """Desenha uma linha curva entre dois estados com a label empilhada, preta e negrito."""
            if origem.nome not in self.positions or destino.nome not in self.positions: return
            x1, y1 = self.positions[origem.nome]
            x2, y2 = self.positions[destino.nome]

            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1
            nx, ny = -dy/dist, dx/dist
            ux, uy = dx/dist, dy/dist

            start_x, start_y = x1 + ux * STATE_RADIUS, y1 + uy * STATE_RADIUS
            end_x, end_y = x2 - ux * STATE_RADIUS, y2 - uy * STATE_RADIUS

            mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            ctrl_x, ctrl_y = mid_x + nx * fator, mid_y + ny * fator

            self.canvas.create_line(start_x, start_y, ctrl_x, ctrl_y, end_x, end_y,
                                    smooth=True, arrow=tk.LAST,
                                    fill=cor_linha, width=largura, tags="linha_transicao")

            text_x = ctrl_x + nx * 15
            text_y = ctrl_y + ny * 15

            # Define a fonte e cor padrão para transições
            transicao_font = (FONT[0], FONT[1], "bold")
            transicao_color = self.canvas_fg_color # Preto

            # --- MODIFICAÇÃO PARA EMPILHAR (usando label_original_virgula) ---
            # Separa os símbolos pela vírgula (formato interno)
            simbolos_lista = label_original_virgula.split(',') # Label já deve estar com formato JFLAP visualmente (ex: ε, a;b) mas junta com vírgula para passar aqui
            # Junta os símbolos com quebra de linha ('\n') para empilhar
            label_empilhada = "\n".join(sorted(simbolos_lista)) # Ordena para consistência visual

            # Cria o texto usando a label empilhada, preta e negrito
            text_id = self.canvas.create_text(
                text_x, text_y,
                text=label_empilhada,
                fill=transicao_color, # Cor preta
                font=transicao_font,  # Fonte negrito
                anchor=tk.CENTER,
                tags=("transition_label_text", label_tag)
            )
            # --- FIM DA MODIFICAÇÃO ---

            bbox = self.canvas.bbox(text_id)
            if bbox: self.label_hitboxes[label_tag] = bbox


    def _agrupar_transicoes(self):
        """Agrupa múltiplas transições entre os mesmos dois estados sob uma única label,
           formatada similarmente ao JFLAP."""
        agrupado = defaultdict(lambda: defaultdict(set))
        if not hasattr(self.automato, 'transicoes'): return agrupado
        trans_dict = self.automato.transicoes
        tipo = self.tipo_automato.get()

        # Define os símbolos para epsilon e vazio/branco conforme JFLAP visualmente
        epsilon_char = "ε" # JFLAP usa lambda, mas epsilon é mais comum
        blank_char = "☐" # Símbolo de branco para Turing (igual ao seu)

        if tipo == "AP":
            for (origem, s_in, s_pop), destinos_set in trans_dict.items():
                if destinos_set is None: continue
                for destino, s_push in destinos_set:
                    # Formato JFLAP: entrada,pop;push (usa epsilon para vazio)
                    in_char = epsilon_char if s_in == EPSILON else s_in
                    pop_char = epsilon_char if s_pop == EPSILON else s_pop
                    push_char = epsilon_char if s_push == EPSILON else s_push
                    label = f"{in_char},{pop_char};{push_char}"
                    agrupado[origem][destino].add(label)
        elif tipo == "Mealy":
             for (origem, simbolo), (destino, output) in trans_dict.items():
                   # Formato JFLAP: entrada/saída (usa epsilon para vazio)
                   in_char = epsilon_char if simbolo == EPSILON else simbolo
                   out_char = epsilon_char if output == EPSILON else output
                   label = f"{in_char}/{out_char}"
                   agrupado[origem][destino].add(label)
        elif tipo == "Turing":
             simbolo_branco_automato = getattr(self.automato, 'simbolo_branco', '☐')
             for (origem, lido), (destino, escrito, direcao) in trans_dict.items():
                   # Formato JFLAP: lido;escrito,direção (usa ☐ para branco)
                   read_char = blank_char if lido == simbolo_branco_automato else lido
                   write_char = blank_char if escrito == simbolo_branco_automato else escrito
                   label = f"{read_char};{write_char},{direcao}"
                   agrupado[origem][destino].add(label)
        else: # AFD, AFN, Moore
            for (origem, simbolo), destinos in trans_dict.items():
                # Formato JFLAP: apenas o símbolo (usa epsilon para vazio)
                label_sym = epsilon_char if simbolo == EPSILON else simbolo
                if isinstance(destinos, set): # AFN
                    for destino in destinos:
                        agrupado[origem][destino].add(label_sym)
                else: # AFD, Moore
                    if destinos:
                        agrupado[origem][destinos].add(label_sym)
        return agrupado

    # --- FUNÇÕES DE SIMULAÇÃO ---
    def iniciar_simulacao(self):
        """Inicia a simulação passo a passo do autômato com a cadeia de entrada."""
        self.parar_simulacao(final_state=False) # Reseta simulação anterior
        cadeia = self.entrada_cadeia.get()
        tipo = self.tipo_automato.get()

        # Limpa labels de status
        self.lbl_cadeia_consumida.configure(text="")
        self.lbl_cadeia_restante.configure(text=cadeia if tipo not in ["Turing"] else "", text_color=self.default_fg_color)
        self.lbl_output_valor.configure(text="")
        self.lbl_tape_valor.configure(text="" if tipo == "Turing" else "")

        try:
            # Validações básicas
            if not self.automato.estados: raise ValueError("O autômato está vazio.")
            if not self.automato.estado_inicial:
                # Tenta definir o primeiro estado criado como inicial se nenhum foi definido
                if self.automato.estados:
                    first_state_name = next(iter(self.automato.estados))
                    print(f"Aviso: Estado inicial não definido. Usando '{first_state_name}' como inicial.")
                    self.automato.definir_estado_inicial(first_state_name)
                    self.desenhar_automato() # Redesenha para mostrar a seta inicial
                else: raise ValueError("Estado inicial não definido e autômato vazio.")

            # Instancia o simulador correto
            if tipo == "AFD": self.simulador = SimuladorAFD(self.automato, cadeia)
            elif tipo == "AFN": self.simulador = SimuladorAFN(self.automato, cadeia)
            elif tipo == "AP": self.simulador = SimuladorAP(self.automato, cadeia)
            elif tipo == "Moore": self.simulador = SimuladorMoore(self.automato, cadeia)
            elif tipo == "Mealy": self.simulador = SimuladorMealy(self.automato, cadeia)
            elif tipo == "Turing": self.simulador = SimuladorMT(self.automato, cadeia)

        except Exception as e: # Captura erros na criação do simulador
            messagebox.showerror("Erro ao Iniciar", str(e)); return

        # Atualiza a UI para o modo de simulação
        self.btn_simular.configure(text="⏹ Parar", command=self.parar_simulacao)
        self.btn_proximo_passo.configure(state="normal") # Habilita botão de passo
        self.lbl_status_simulacao.configure(text="Simulando...", text_color=self.default_fg_color)
        self.executar_proximo_passo() # Executa o primeiro passo automaticamente

    def parar_simulacao(self, final_state=False):
        """Para a simulação atual e reseta a UI para o estado inicial."""
        self.simulador = None # Descarta o objeto simulador
        # Restaura botão 'Iniciar' e desabilita 'Passo'
        self.btn_simular.configure(text="▶ Iniciar", command=self.iniciar_simulacao)
        self.btn_proximo_passo.configure(state="disabled")
        # Se não parou em um estado final (aceita/rejeita), limpa tudo
        if not final_state:
            self.lbl_status_simulacao.configure(text="Status: Aguardando", text_color=self.default_fg_color)
            self.lbl_cadeia_consumida.configure(text="")
            self.lbl_cadeia_restante.configure(text="", text_color=self.default_fg_color)
            self.lbl_output_valor.configure(text="")
            self.lbl_tape_valor.configure(text="")
            self.desenhar_automato() # Remove destaques do canvas

    def executar_proximo_passo(self):
        """Executa o próximo passo da simulação e atualiza a UI."""
        if not self.simulador: return # Não faz nada se a simulação não está ativa

        passo_info = self.simulador.proximo_passo() # Obtém informações do próximo passo
        tipo = self.tipo_automato.get()

        # Se não há mais passos (simulação terminou)
        if not passo_info:
            current_status_text = self.lbl_status_simulacao.cget("text")
            # Se ainda estava "Simulando", verifica se terminou em estado de aceitação
            if current_status_text == "Simulando..." or current_status_text == "Status: Aguardando":
                aceitou = False
                try: # Tenta acessar o último estado do gerador para verificar se é final
                    last_step_vars = self.simulador.gerador.gi_frame.f_locals
                    # Pega 'estado_atual' ou 'estados_atuais' dependendo do tipo de simulador
                    last_active_states = last_step_vars.get('estado_atual', last_step_vars.get('estados_atuais', set()))
                    if last_active_states and hasattr(self.simulador, 'automato') and self.simulador.automato.estados_finais:
                        # Verifica se algum dos últimos estados ativos é um estado final
                        aceitou = any(self.simulador.automato.estados[e] in self.simulador.automato.estados_finais
                                        for e in last_active_states if e in self.simulador.automato.estados)
                except Exception as e: # Erro ao acessar variáveis internas do gerador (raro)
                    print(f"Erro ao verificar estado final: {e}")

                # Atualiza o status final (Aceita/Não Aceita)
                if aceitou: self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita)
                else: self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita)

            self.parar_simulacao(final_state=True) # Para a simulação, mantendo o status final
            return

        # Processa as informações do passo atual
        status = passo_info["status"]
        extra_info_canvas = None # Informação extra a ser exibida no canvas (pilha/fita)

        # Atualiza label da Fita (Turing)
        if "tape" in passo_info and passo_info["tape"] is not None:
            self.lbl_tape_valor.configure(text=passo_info["tape"])
            extra_info_canvas = passo_info["tape"]

        # Atualiza label de Saída (Moore/Mealy)
        if "output" in passo_info and passo_info["output"] is not None:
            self.lbl_output_valor.configure(text=passo_info["output"])

        # Define informação extra para Pilha (AP)
        if "pilha" in passo_info and passo_info["pilha"] is not None:
             extra_info_canvas = passo_info["pilha"]

        # Atualiza labels de cadeia consumida/restante (exceto Turing)
        if "cadeia_restante" in passo_info and tipo != "Turing":
            cadeia_restante = passo_info['cadeia_restante']
            cadeia_original = self.entrada_cadeia.get()
            # Calcula o ponto de divisão entre consumido e restante
            split_point = len(cadeia_original) - len(cadeia_restante)
            cadeia_consumida = cadeia_original[:split_point]
            self.lbl_cadeia_consumida.configure(text=cadeia_consumida)
            self.lbl_cadeia_restante.configure(text=cadeia_restante, text_color=self.default_fg_color)
        elif tipo == "Turing": # Turing não usa essas labels
             self.lbl_cadeia_consumida.configure(text="")
             self.lbl_cadeia_restante.configure(text="")

        # Atualiza o canvas e status com base no resultado do passo
        if status == "executando":
            # Redesenha destacando estado(s) e transição(ões) atuais
            self.desenhar_automato(passo_info["estado_atual"], passo_info.get("transicao_ativa"), extra_info_canvas)
        elif status == "aceita":
            self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita)
            # Mostra toda a cadeia como consumida
            if tipo != "Turing": self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get()); self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True) # Para mantendo o status
        elif status == "rejeita":
            self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita)
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True) # Para mantendo o status
        elif status == "finalizado": # Usado por Moore/Mealy
            self.lbl_status_simulacao.configure(text="Processamento Concluído", text_color=self.cor_finalizado)
            if tipo != "Turing": self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get()); self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True) # Para mantendo o status
        elif status == "erro": # Erro durante a simulação
            messagebox.showerror("Erro", passo_info["mensagem"])
            self.parar_simulacao() # Para e reseta a UI


    # --- MÉTODOS DE EXPORTAÇÃO ---
    def exportar_para_jpg(self):
        """Salva a área atual do canvas como uma imagem JPG."""
        # Verifica se há algo para exportar
        if not self.automato or not self.automato.estados:
             messagebox.showwarning("Exportar JPG", "Não há autômato para exportar.", parent=self.master)
             return

        try:
            # Abre diálogo para escolher local e nome do arquivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")],
                title="Salvar Autômato como JPG",
                parent=self.master
            )
            if not filepath: return # Cancelou

            # Captura a imagem da área do canvas
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            margin = 2 # Pequena margem para não cortar bordas
            img = ImageGrab.grab(bbox=(x + margin, y + margin, x1 - margin, y1 - margin))
            img.save(filepath, "JPEG") # Salva a imagem
            messagebox.showinfo("Exportar JPG", f"Autômato salvo como JPG em:\n{filepath}", parent=self.master)
        except Exception as e: # Captura erros ao salvar
            messagebox.showerror("Erro ao Exportar JPG", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JPG: {e}")


    def exportar_para_jff(self):
        """Converte o autômato atual para o formato JFLAP (.jff) e salva em arquivo."""
        # Verifica se há algo para exportar
        if not self.automato or not self.automato.estados:
            messagebox.showwarning("Exportar JFF", "Não há autômato para exportar.", parent=self.master)
            return

        # Mapeia o tipo interno para o tipo JFLAP
        automato_tipo = self.tipo_automato.get().lower()
        jflap_type = "fa" # Padrão para AFD/AFN
        if automato_tipo == "ap": jflap_type = "pda"
        elif automato_tipo == "turing": jflap_type = "turing"
        elif automato_tipo in ["moore", "mealy"]: jflap_type = "mealy" # JFLAP usa 'mealy' para ambos

        try:
            # Abre diálogo para escolher local e nome do arquivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jff",
                filetypes=[("JFLAP files", "*.jff"), ("All files", "*.*")],
                title="Salvar Autômato como JFF",
                parent=self.master
            )
            if not filepath: return # Cancelou

            # Cria a estrutura XML raiz
            root = ET.Element("structure")
            ET.SubElement(root, "type").text = jflap_type
            automaton_element = ET.SubElement(root, "automaton")
            # Mapeia nomes de estado para IDs numéricos (JFLAP requer IDs)
            state_to_id = {name: str(i) for i, name in enumerate(self.automato.estados.keys())}

            # Adiciona cada estado ao XML
            for name, estado in self.automato.estados.items():
                state_id = state_to_id[name]
                state_element = ET.SubElement(automaton_element, "state", id=state_id, name=name)
                # Pega a posição do estado ou define uma padrão se não existir
                x_pos, y_pos = self.positions.get(name, (50.0 + int(state_id)*80, 50.0))
                ET.SubElement(state_element, "x").text = str(float(x_pos))
                ET.SubElement(state_element, "y").text = str(float(y_pos))
                # Adiciona tags <initial/> e/ou <final/> se aplicável
                if estado.is_inicial:
                    ET.SubElement(state_element, "initial")
                if estado.is_final:
                    ET.SubElement(state_element, "final")
                # Adiciona tag <output> para Moore
                if automato_tipo == "moore" and hasattr(estado, 'output') and estado.output:
                     ET.SubElement(state_element, "output").text = estado.output

            # Adiciona as transições ao XML (lógica varia por tipo)
            if jflap_type == "fa": # AFD/AFN
                for (origem, simbolo), destinos in self.automato.transicoes.items():
                    origem_id = state_to_id.get(origem)
                    if origem_id is None: continue
                    # Garante que destinos seja um conjunto (para AFN)
                    destinos_set = destinos if isinstance(destinos, set) else {destinos}
                    for destino in destinos_set:
                        destino_id = state_to_id.get(destino)
                        if destino_id is None: continue
                        trans_element = ET.SubElement(automaton_element, "transition")
                        ET.SubElement(trans_element, "from").text = origem_id
                        ET.SubElement(trans_element, "to").text = destino_id
                        read_element = ET.SubElement(trans_element, "read")
                        if simbolo != EPSILON: read_element.text = simbolo # JFLAP usa <read/> vazio para epsilon
            elif jflap_type == "pda": # AP
                 for (origem, s_in, s_pop), destinos_push in self.automato.transicoes.items():
                     origem_id = state_to_id.get(origem)
                     if origem_id is None: continue
                     for destino, s_push in destinos_push:
                         destino_id = state_to_id.get(destino)
                         if destino_id is None: continue
                         trans_element = ET.SubElement(automaton_element, "transition")
                         ET.SubElement(trans_element, "from").text = origem_id
                         ET.SubElement(trans_element, "to").text = destino_id
                         read_element = ET.SubElement(trans_element, "read")
                         if s_in != EPSILON: read_element.text = s_in
                         pop_element = ET.SubElement(trans_element, "pop")
                         if s_pop != EPSILON: pop_element.text = s_pop
                         push_element = ET.SubElement(trans_element, "push")
                         if s_push != EPSILON: push_element.text = s_push
            elif jflap_type == "turing": # Turing
                 simbolo_branco_automato = getattr(self.automato, 'simbolo_branco', 'B') # Usa o símbolo branco definido ou 'B'
                 for (origem, lido), (destino, escrito, direcao) in self.automato.transicoes.items():
                     origem_id = state_to_id.get(origem)
                     destino_id = state_to_id.get(destino)
                     if origem_id is None or destino_id is None: continue
                     trans_element = ET.SubElement(automaton_element, "transition")
                     ET.SubElement(trans_element, "from").text = origem_id
                     ET.SubElement(trans_element, "to").text = destino_id
                     read_element = ET.SubElement(trans_element, "read")
                     # JFLAP usa <read/> vazio para símbolo branco
                     if lido != simbolo_branco_automato: read_element.text = lido
                     write_element = ET.SubElement(trans_element, "write")
                     if escrito != simbolo_branco_automato: write_element.text = escrito
                     move_element = ET.SubElement(trans_element, "move")
                     move_element.text = direcao
            elif jflap_type == "mealy": # Mealy (e Moore, pois JFLAP não diferencia na exportação)
                 for (origem, simbolo), (destino, output) in self.automato.transicoes.items():
                    origem_id = state_to_id.get(origem)
                    destino_id = state_to_id.get(destino)
                    if origem_id is None or destino_id is None: continue
                    trans_element = ET.SubElement(automaton_element, "transition")
                    ET.SubElement(trans_element, "from").text = origem_id
                    ET.SubElement(trans_element, "to").text = destino_id
                    read_element = ET.SubElement(trans_element, "read")
                    if simbolo != EPSILON: read_element.text = simbolo
                    output_element = ET.SubElement(trans_element, "transout") # Saída da transição
                    if output != EPSILON: output_element.text = output

            # Formata o XML para ficar legível (indentação)
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml_str = dom.toprettyxml(indent="  ")

            # Salva o XML formatado no arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                # Adiciona a declaração XML manualmente (minidom não faz isso bem)
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                # Escreve o restante do XML (pulando a declaração duplicada, se houver)
                f.write(pretty_xml_str.split('\n', 1)[1])

            messagebox.showinfo("Exportar JFF", f"Autômato salvo como JFF em:\n{filepath}", parent=self.master)

        except Exception as e: # Captura erros durante a criação ou escrita do XML
            messagebox.showerror("Erro ao Exportar JFF", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JFF: {e}")


# --- CLASSES DE DIÁLOGO ---
# Diálogos modais para inserir informações de transição

class TransicaoPilhaDialog(ctk.CTkToplevel):
    """Diálogo para criar/editar transições de Autômato de Pilha."""
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição AP")
        self.resultado = None # Armazena os dados inseridos
        self.geometry("300x350")
        if style_dict is None: style_dict = {}

        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))

        # Campos de entrada
        ctk.CTkLabel(self, text="Entrada (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_entrada = ctk.CTkEntry(self, **style_dict)
        self.e_entrada.pack(padx=20, pady=5)
        self.e_entrada.insert(0, 'e') # Valor padrão

        ctk.CTkLabel(self, text="Desempilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_pop = ctk.CTkEntry(self, **style_dict)
        self.e_pop.pack(padx=20, pady=5)
        self.e_pop.insert(0, 'e')

        ctk.CTkLabel(self, text="Empilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_push = ctk.CTkEntry(self, **style_dict)
        self.e_push.pack(padx=20, pady=5)
        self.e_push.insert(0, 'e')

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set() # Torna o diálogo modal
        self.e_entrada.focus() # Foco no primeiro campo

    def ok(self):
        """Chamado ao clicar OK. Processa e armazena os dados, depois fecha."""
        # Obtém valores, tratando 'e' como EPSILON
        self.resultado = {
            'entrada': EPSILON if (ent := self.e_entrada.get()) == 'e' else ent,
            'pop': EPSILON if (pop := self.e_pop.get()) == 'e' else pop,
            'push': EPSILON if (push := self.e_push.get()) == 'e' else push
        }
        self.destroy() # Fecha o diálogo

class TransicaoMealyDialog(ctk.CTkToplevel):
    """Diálogo para criar/editar transições de Máquina de Mealy."""
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição Mealy")
        self.resultado = None
        self.geometry("300x280")
        if style_dict is None: style_dict = {}

        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))

        ctk.CTkLabel(self, text="Símbolo de Entrada (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_simbolo = ctk.CTkEntry(self, **style_dict)
        self.e_simbolo.pack(padx=20, pady=5)
        self.e_simbolo.insert(0, 'e')

        ctk.CTkLabel(self, text="Símbolo de Saída (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_output = ctk.CTkEntry(self, **style_dict)
        self.e_output.pack(padx=20, pady=5)
        self.e_output.insert(0, 'e')

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set()
        self.e_simbolo.focus()

    def ok(self):
        """Processa entrada/saída e fecha o diálogo."""
        simbolo_input = self.e_simbolo.get()
        output_input = self.e_output.get()
        # Usa 'e' como valor padrão se campo estiver vazio
        simbolo_final = simbolo_input if simbolo_input else 'e'
        output_final = output_input if output_input else 'e'
        self.resultado = {
            'simbolo': simbolo_final,
            'output': output_final
        }
        self.destroy()

class TransicaoTuringDialog(ctk.CTkToplevel):
    """Diálogo para criar/editar transições de Máquina de Turing."""
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição Turing")
        self.resultado = None
        self.geometry("300x350")
        if style_dict is None: style_dict = {}

        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))

        ctk.CTkLabel(self, text="Símbolo Lido:").pack(padx=20, pady=(10,0))
        self.e_lido = ctk.CTkEntry(self, **style_dict)
        self.e_lido.pack(padx=20, pady=5)
        self.e_lido.insert(0, '☐') # Usa símbolo de branco como padrão

        ctk.CTkLabel(self, text="Símbolo Escrito:").pack(padx=20, pady=(10,0))
        self.e_escrito = ctk.CTkEntry(self, **style_dict)
        self.e_escrito.pack(padx=20, pady=5)
        self.e_escrito.insert(0, '☐')

        ctk.CTkLabel(self, text="Direção (L/R):").pack(padx=20, pady=(10,0))
        self.e_dir = ctk.CTkEntry(self, width=50, **style_dict) # Campo mais estreito
        self.e_dir.pack(padx=20, pady=5)
        self.e_dir.insert(0, 'R') # Direita como padrão

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set()
        self.e_lido.focus()

    def ok(self):
        """Valida e processa os dados da transição de Turing."""
        lido = self.e_lido.get() or '☐' # Usa branco se vazio
        escrito = self.e_escrito.get() or '☐'
        direcao = (self.e_dir.get() or 'R').upper() # Pega, padroniza para 'R' se vazio, e converte para maiúscula

        # Validações
        if direcao not in ['L', 'R']:
            messagebox.showerror("Erro", "Direção deve ser 'L' ou 'R'.", parent=self)
            return
        if len(lido) > 1 or len(escrito) > 1:
             messagebox.showerror("Erro", "Símbolos da fita devem ter apenas 1 caractere.", parent=self)
             return

        # Armazena e fecha
        self.resultado = {'lido': lido, 'escrito': escrito, 'dir': direcao}
        self.destroy()