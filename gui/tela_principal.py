import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import math
from automato.automato_finito import AFD, AFN
from automato.automato_pilha import AutomatoPilha
# --- NOVAS IMPORTAÇÕES ---
from automato.maquinas_moore_mealy import MaquinaMoore, MaquinaMealy
from automato.maquina_turing import MaquinaTuring
from automato import EPSILON
from simulador.simulador_passos import (
    SimuladorAFD, SimuladorAFN, SimuladorAP,
    SimuladorMoore, SimuladorMealy, SimuladorMT
)
# --- FIM DAS NOVAS IMPORTAÇÕES ---
from collections import defaultdict

STATE_RADIUS = 25
FONT = ("Segoe UI", 10)

class TelaPrincipal:
    def __init__(self, master, voltar_menu_callback=None):
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
                                        text="Limpar Tudo",
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

        btn_inicial = ctk.CTkButton(tool_bar, text="► Inicial",
                                      command=lambda mid="INICIAL": self.set_active_mode(mid),
                                      fg_color=self.cor_ferramenta_fg,
                                      hover_color=self.cor_ferramenta_hover,
                                      **self.style_tool_button)
        btn_inicial.pack(side="left", padx=5, pady=5)
        self.tool_buttons["INICIAL"] = btn_inicial

        btn_final = ctk.CTkButton(tool_bar, text="◎ Final",
                                    command=lambda mid="FINAL": self.set_active_mode(mid),
                                    fg_color=self.cor_ferramenta_fg,
                                    hover_color=self.cor_ferramenta_hover,
                                    **self.style_tool_button)
        btn_final.pack(side="left", padx=5, pady=5)
        self.tool_buttons["FINAL"] = btn_final

        btn_estado = ctk.CTkButton(tool_bar, text="○ Estado",
                                     command=lambda mid="ESTADO": self.set_active_mode(mid),
                                     fg_color=self.cor_ferramenta_fg,
                                     hover_color=self.cor_ferramenta_hover,
                                     **self.style_tool_button)
        btn_estado.pack(side="left", padx=5, pady=5)
        self.tool_buttons["ESTADO"] = btn_estado

        btn_deletar = ctk.CTkButton(tool_bar, text="❌ Deletar",
                                      command=lambda mid="DELETAR": self.set_active_mode(mid),
                                      fg_color=self.cor_destrutiva_fg,
                                      hover_color=self.cor_destrutiva_hover,
                                      **self.style_tool_button)
        btn_deletar.pack(side="left", padx=5, pady=5)
        self.tool_buttons["DELETAR"] = btn_deletar

        btn_mover = ctk.CTkButton(tool_bar, text="✥ Mover/Editar",
                                    command=lambda mid="MOVER": self.set_active_mode(mid),
                                    fg_color=self.cor_ferramenta_fg,
                                    hover_color=self.cor_ferramenta_hover,
                                    **self.style_tool_button)
        btn_mover.pack(side="left", padx=5, pady=5)
        self.tool_buttons["MOVER"] = btn_mover

        btn_transicao = ctk.CTkButton(tool_bar, text="→ Transição",
                                        command=lambda mid="TRANSICAO": self.set_active_mode(mid),
                                        fg_color=self.cor_ferramenta_fg,
                                        hover_color=self.cor_ferramenta_hover,
                                        **self.style_tool_button)
        btn_transicao.pack(side="left", padx=5, pady=5)
        self.tool_buttons["TRANSICAO"] = btn_transicao


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

        self.lbl_cadeia_consumida = ctk.CTkLabel(cadeia_status_frame, text="", text_color=self.cor_consumida, font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_cadeia_consumida.pack(side="left")

        self.lbl_cadeia_restante = ctk.CTkLabel(cadeia_status_frame, text="", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_cadeia_restante.pack(side="left")

        self.lbl_status_simulacao = ctk.CTkLabel(frame_simulacao, text="Status: Aguardando", font=ctk.CTkFont(weight="bold"))
        self.lbl_status_simulacao.grid(row=0, column=5, padx=10, pady=10, sticky="e")

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
        if mode_id == self.current_mode: self.current_mode = "MOVER"
        else: self.current_mode = mode_id
        self.update_button_styles()
        self.update_cursor_and_status()

    def update_button_styles(self):
        for mode_id, button in self.tool_buttons.items():
            is_active = (mode_id == self.current_mode)

            if mode_id == "DELETAR":
                color = self.cor_destrutiva_hover if is_active else self.cor_destrutiva_fg
                button.configure(fg_color=color)
            else:
                color = self.cor_ferramenta_hover if is_active else self.cor_ferramenta_fg
                button.configure(fg_color=color)

    def update_cursor_and_status(self):
        mode = self.current_mode
        cursor_map = { "ESTADO": "crosshair", "TRANSICAO": "hand2", "INICIAL": "arrow",
                       "FINAL": "star", "MOVER": "fleur", "DELETAR": "X_cursor" }
        self.master.config(cursor=cursor_map.get(mode, "arrow"))
        self.origem_transicao = None

    # --- FUNÇÕES DE TEMA ---
    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

        self.update_theme_button_text()

        self.default_fg_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        self.update_button_styles()
        self.desenhar_automato()

    def voltar_ao_menu(self):
        if self.voltar_menu_callback:
            if self.simulador:
                self.parar_simulacao()
            for widget in self.master.winfo_children():
                widget.destroy()
            self.voltar_menu_callback()

    def update_theme_button_text(self):
        current_mode = ctk.get_appearance_mode()

        if current_mode == "Dark":
            button_text = "Modo Claro ☀️"
            btn_fg_color = "#F0F0F0"
            btn_hover_color = "#D5D5D5"
            btn_text_color = "#1A1A1A"
        else:
            button_text = "Modo Escuro 🌙"
            btn_fg_color = "#333333"
            btn_hover_color = "#4A4A4A"
            btn_text_color = "#E0E0E0"

        self.btn_theme_toggle.configure(
            text=button_text,
            fg_color=btn_fg_color,
            hover_color=btn_hover_color,
            text_color=btn_text_color
        )

    # --- FUNÇÕES DE UI ---

    def _atualizar_widgets_extra_info(self):
        tipo = self.tipo_automato.get()
        self.lbl_output_tag.grid_remove()
        self.lbl_output_valor.grid_remove()
        self.lbl_tape_tag.grid_remove()
        self.lbl_tape_valor.grid_remove()

        if tipo in ["Moore", "Mealy"]:
            self.lbl_output_tag.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
            self.lbl_output_valor.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        elif tipo == "Turing":
            self.lbl_tape_tag.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
            self.lbl_tape_valor.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        if tipo in ["AFD", "AFN", "AP"]:
             self.frame_extra_info.grid_remove()
        else:
             self.frame_extra_info.grid()

    def mudar_tipo_automato(self, event=None):
        self.limpar_tela()
        self._atualizar_widgets_extra_info()

    def limpar_tela(self):
        self.contador_estados = 0
        tipo = self.tipo_automato.get()
        if tipo == "AFD": self.automato = AFD()
        elif tipo == "AFN": self.automato = AFN()
        elif tipo == "AP": self.automato = AutomatoPilha()
        elif tipo == "Moore": self.automato = MaquinaMoore()
        elif tipo == "Mealy": self.automato = MaquinaMealy()
        elif tipo == "Turing": self.automato = MaquinaTuring()

        self.positions = {}
        self.parar_simulacao(final_state=False)
        self.set_active_mode("MOVER")
        self.desenhar_automato()
        self._atualizar_widgets_extra_info()


    # <-- ATUALIZAÇÃO: Verificações messagebox.askyesno removidas -->
    def clique_canvas(self, event):
        mode = self.current_mode
        estado_clicado = self._get_estado_em(event.x, event.y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y)

        if mode == "ESTADO" and not estado_clicado and not transicao_clicada:
            nome_estado = f"q{self.contador_estados}"
            while nome_estado in self.automato.estados:
                self.contador_estados += 1; nome_estado = f"q{self.contador_estados}"

            if self.tipo_automato.get() == "Moore":
                dialog = ctk.CTkInputDialog(text="Símbolo de Saída do Estado (vazio=default):", title="Criar Estado Moore")
                output = dialog.get_input()
                if output is None: return
                self.automato.adicionar_estado(nome_estado, event.x, event.y, output=output)
            else:
                self.automato.adicionar_estado(nome_estado, event.x, event.y)

            self.positions[nome_estado] = (event.x, event.y)
            self.contador_estados += 1
        elif estado_clicado:
            if mode == "TRANSICAO":
                if not self.origem_transicao:
                    self.origem_transicao = estado_clicado
                else:
                    self._criar_transicao(self.origem_transicao, estado_clicado)
                    self.origem_transicao = None
            elif mode == "INICIAL": self.automato.definir_estado_inicial(estado_clicado.nome)
            elif mode == "FINAL": self.automato.alternar_estado_final(estado_clicado.nome)
            elif mode == "MOVER": self.estado_movendo = estado_clicado
            elif mode == "DELETAR":
                # --- REMOVIDO: if messagebox.askyesno(...) ---
                nome_a_deletar = estado_clicado.nome
                self.automato.deletar_estado(nome_a_deletar)
                self.positions.pop(nome_a_deletar, None)
                # --- FIM DA REMOÇÃO ---
            else: pass
        elif transicao_clicada and mode == "DELETAR":
            origem, destino = transicao_clicada
            # --- REMOVIDO: if messagebox.askyesno(...) ---
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            else: print(f"Aviso: Método 'deletar_transicoes_entre' não implementado para {type(self.automato)}")
            # --- FIM DA REMOÇÃO ---
        elif not estado_clicado and not transicao_clicada:
            self.origem_transicao = None

        self.desenhar_automato()
    # <-- FIM DA ATUALIZAÇÃO -->


    def duplo_clique_canvas(self, event):
        mode = self.current_mode
        estado_clicado = self._get_estado_em(event.x, event.y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y)

        if estado_clicado and mode == "MOVER":
            novo_nome = ctk.CTkInputDialog(text="Digite o novo nome do estado:", title="Renomear Estado").get_input()

            if self.tipo_automato.get() == "Moore":
                novo_output = ctk.CTkInputDialog(text="Digite a nova saída do estado:", title="Editar Saída Moore").get_input()
                if novo_output is not None:
                    self.automato.set_output_estado(estado_clicado.nome, novo_output)

            if novo_nome and novo_nome != estado_clicado.nome:
                try:
                    pos = self.positions.pop(estado_clicado.nome)
                    self.automato.renomear_estado(estado_clicado.nome, novo_nome)
                    self.positions[novo_nome] = pos
                except ValueError as e:
                    messagebox.showerror("Erro ao Renomear", str(e))
                    if estado_clicado.nome in self.automato.estados: self.positions[estado_clicado.nome] = pos
            self.desenhar_automato()
        elif transicao_clicada and mode == "MOVER":
            origem, destino = transicao_clicada
            self._editar_label_transicao(origem, destino)


    def _editar_label_transicao(self, origem, destino):
        tipo = self.tipo_automato.get()
        if tipo in ["AP", "Mealy", "Turing"]:
            messagebox.showinfo("Editar Transição", f"Edição de transições {tipo} não implementada com duplo clique. Use Deletar e Criar.", parent=self.master)
            return

        simbolos_atuais = set()
        agrupado = self._agrupar_transicoes()
        if origem in agrupado and destino in agrupado[origem]:
            simbolos_atuais = agrupado[origem][destino]

        label_atual = ",".join(sorted(list(s.replace(EPSILON, "e") for s in simbolos_atuais)))

        dialog = ctk.CTkInputDialog(text="Símbolo(s) (use 'e' para ε, vírgula para separar):", title="Editar Transição")
        dialog.entry.insert(0, label_atual)
        simbolo_input = dialog.get_input()

        if simbolo_input is not None:
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            novos_simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
            for s in novos_simbolos:
                simbolo_final = EPSILON if s == 'e' else s
                self.automato.adicionar_transicao(origem, simbolo_final, destino)
            self.desenhar_automato()


    def _criar_transicao(self, origem, destino):
        tipo = self.tipo_automato.get()

        if tipo in ["AFD", "AFN", "Moore"]:
            dialog = ctk.CTkInputDialog(text="Símbolo(s) (use 'e' para ε, vírgula para separar):", title=f"Criar Transição {tipo}")
            simbolo_input = dialog.get_input()
            if simbolo_input is not None:
                simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
                for s in simbolos:
                    simbolo_final = EPSILON if s == 'e' else s
                    self.automato.adicionar_transicao(origem.nome, simbolo_final, destino.nome)

        elif tipo == "AP":
            dlg = TransicaoPilhaDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['entrada'], dlg.resultado['pop'], destino.nome, dlg.resultado['push'])

        elif tipo == "Mealy":
            dlg = TransicaoMealyDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                simbolo = EPSILON if dlg.resultado['simbolo'] == 'e' else dlg.resultado['simbolo']
                output = EPSILON if dlg.resultado['output'] == 'e' else dlg.resultado['output']
                self.automato.adicionar_transicao(origem.nome, simbolo, destino.nome, output)

        elif tipo == "Turing":
            dlg = TransicaoTuringDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['lido'], destino.nome, dlg.resultado['escrito'], dlg.resultado['dir'])

        self.desenhar_automato()

    # --- Funções de Arrastar/Soltar ---
    def arrastar_canvas(self, event):
        if self.estado_movendo and self.estado_movendo.nome in self.positions:
            self.positions[self.estado_movendo.nome] = (event.x, event.y)
            self.desenhar_automato()
    def soltar_canvas(self, event):
        self.estado_movendo = None

    # --- Funções _get ---
    def _get_estado_em(self, x, y):
        for nome, (sx, sy) in self.positions.items():
            if (sx - x)**2 + (sy - y)**2 <= (STATE_RADIUS + 2)**2:
                if nome in self.automato.estados: return self.automato.estados[nome]
        return None

    def _get_transicao_label_em(self, x, y):
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item_id in reversed(items):
            tags = self.canvas.gettags(item_id)
            if "transition_label" in tags:
                for tag in tags:
                    if tag.startswith("label_"):
                        parts = tag.split('_')
                        if len(parts) == 3: return parts[1], parts[2]
        return None

    # --- FUNÇÕES DE DESENHO ---

    def desenhar_automato(self, estados_ativos=None, transicoes_ativas=None, extra_info_str=None):
        try:
            self.canvas.delete("all")
            self.label_hitboxes.clear()
            transicoes_ativas = transicoes_ativas or set()
            agrupado = self._agrupar_transicoes()
            pares_processados = set()
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
                    par = tuple(sorted((origem_nome, destino_nome)))

                    cor_linha = self.canvas_transicao_ativa if (origem_nome, destino_nome) in transicoes_ativas else self.canvas_fg_color
                    largura = 2.5 if cor_linha == self.canvas_transicao_ativa else 1.5
                    label = ",".join(sorted(list(simbolos))).replace(EPSILON, "ε")
                    label_tag = f"label_{origem_nome}_{destino_nome}"

                    if origem_nome == destino_nome: # Loop
                        text_id = self.canvas.create_text(x1, y1 - 55, text=label, fill=self.canvas_transicao_text, font=FONT, tags=("texto", "transition_label", label_tag))
                        p1_x, p1_y = x1 - 10, y1 - STATE_RADIUS
                        c1_x, c1_y = x1 - 40, y1 - (STATE_RADIUS + 35)
                        c2_x, c2_y = x1 + 40, y1 - (STATE_RADIUS + 35)
                        p2_x, p2_y = x1 + 10, y1 - STATE_RADIUS
                        self.canvas.create_line(p1_x, p1_y, c1_x, c1_y, c2_x, c2_y, p2_x, p2_y,
                                                smooth=True, arrow=tk.LAST,
                                                fill=cor_linha, width=largura, tags="linha")
                        bbox = self.canvas.bbox(text_id)
                        if bbox: self.label_hitboxes[label_tag] = bbox

                    elif agrupado.get(destino_nome, {}).get(origem_nome): # Transição dupla
                        if par in pares_processados: continue
                        cor_linha_volta = self.canvas_transicao_ativa if (destino_nome, origem_nome) in transicoes_ativas else self.canvas_fg_color
                        largura_volta = 2.5 if cor_linha_volta == self.canvas_transicao_ativa else 1.5
                        label_tag_volta = f"label_{destino_nome}_{origem_nome}"
                        self._desenhar_linha_curva(origem, destino, label, 30, cor_linha, largura, label_tag)
                        label_volta = ",".join(sorted(list(agrupado[destino_nome][origem_nome]))).replace(EPSILON, "ε")
                        self._desenhar_linha_curva(destino, origem, label_volta, 30, cor_linha_volta, largura_volta, label_tag_volta)
                        pares_processados.add(par)
                    else: # Transição reta simples
                        dx, dy = x2 - x1, y2 - y1
                        dist = math.hypot(dx, dy) or 1
                        ux, uy = dx/dist, dy/dist
                        start_x, start_y = x1 + ux * STATE_RADIUS, y1 + uy * STATE_RADIUS
                        end_x, end_y = x2 - ux * STATE_RADIUS, y2 - uy * STATE_RADIUS
                        self.canvas.create_line(start_x, start_y, end_x, end_y,
                                                arrow=tk.LAST,
                                                fill=cor_linha, width=largura, tags="linha")
                        text_x = (start_x+end_x)/2 - uy*10
                        text_y = (start_y+end_y)/2 + ux*10
                        text_id = self.canvas.create_text(text_x, text_y, text=label, fill=self.canvas_transicao_text, font=FONT, tags=("texto", "transition_label", label_tag))
                        bbox = self.canvas.bbox(text_id)
                        if bbox: self.label_hitboxes[label_tag] = bbox

            # --- DESENHAR ESTADOS ---
            for nome, estado in self.automato.estados.items():
                if nome not in self.positions: continue
                x, y = self.positions[nome]
                cor_borda = self.canvas_estado_ativo if estados_ativos and nome in estados_ativos else self.canvas_fg_color
                self.canvas.create_oval(x - STATE_RADIUS, y - STATE_RADIUS, x + STATE_RADIUS, y + STATE_RADIUS,
                                        fill=self.canvas_estado_fill, outline=cor_borda,
                                        width=3 if cor_borda == self.canvas_estado_ativo else 2)

                texto_estado = nome
                if tipo == "Moore" and estado.output:
                    texto_estado = f"{nome}\n({estado.output})"
                self.canvas.create_text(x, y, text=texto_estado, font=FONT, fill=self.canvas_estado_text, justify=tk.CENTER)

                if estado.is_final:
                    self.canvas.create_oval(x - (STATE_RADIUS - 5), y - (STATE_RADIUS - 5),
                                            x + (STATE_RADIUS - 5), y + (STATE_RADIUS - 5),
                                            outline=cor_borda, width=1)
                if estado.is_inicial:
                    self.canvas.create_line(x - STATE_RADIUS - 20, y, x - STATE_RADIUS, y,
                                            arrow=tk.LAST,
                                            width=2, fill=self.canvas_fg_color)

            # --- OUTROS ELEMENTOS ---
            if self.origem_transicao and self.origem_transicao.nome in self.positions:
                x, y = self.positions[self.origem_transicao.nome]
                self.canvas.create_oval(x-STATE_RADIUS-3, y-STATE_RADIUS-3, x+STATE_RADIUS+3, y+STATE_RADIUS+3, outline="#33cc33", width=2, dash=(4, 4))

            if extra_info_str is not None:
                tag = "Pilha: " if tipo == "AP" else ("Fita: " if tipo == "Turing" else "")
                if tag:
                    self.canvas.create_rectangle(10, 10, 10 + len(tag + extra_info_str) * 8, 40, fill="#f0f0f0", outline="")
                    self.canvas.create_text(15, 25, text=f"{tag}{extra_info_str}", font=FONT, fill=self.canvas_fg_color, anchor="w")

        except Exception as e:
            print(f"Erro crítico ao desenhar automato: {e}")

    def _desenhar_linha_curva(self, origem, destino, label, fator, cor_linha, largura, label_tag):
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
                                fill=cor_linha, width=largura, tags="linha")

        text_x = ctrl_x + nx * 10
        text_y = ctrl_y + ny * 10
        text_id = self.canvas.create_text(text_x, text_y, text=label, fill=self.canvas_transicao_text, font=FONT, tags=("texto", "transition_label", label_tag))
        bbox = self.canvas.bbox(text_id)
        if bbox: self.label_hitboxes[label_tag] = bbox


    def _agrupar_transicoes(self):
        agrupado = defaultdict(lambda: defaultdict(set))
        if not hasattr(self.automato, 'transicoes'): return agrupado
        trans_dict = self.automato.transicoes
        tipo = self.tipo_automato.get()

        if tipo == "AP":
            for (origem, s_in, s_pop), destinos_set in trans_dict.items():
                if destinos_set is None: continue
                for destino, s_push in destinos_set:
                    label = f"{s_in},{s_pop}→{s_push}"
                    agrupado[origem][destino].add(label)
        elif tipo == "Mealy":
             for (origem, simbolo), (destino, output) in trans_dict.items():
                   label = f"{simbolo}/{output}"
                   agrupado[origem][destino].add(label)
        elif tipo == "Turing":
             for (origem, lido), (destino, escrito, direcao) in trans_dict.items():
                   label = f"{lido}→{escrito},{direcao}"
                   agrupado[origem][destino].add(label)
        else: # AFD, AFN, Moore
            for (origem, simbolo), destinos in trans_dict.items():
                label_sym = simbolo
                if isinstance(destinos, set): # AFN
                    for destino in destinos:
                        agrupado[origem][destino].add(label_sym)
                else: # AFD, Moore
                    if destinos:
                        agrupado[origem][destinos].add(label_sym)
        return agrupado


    # --- FUNÇÕES DE SIMULAÇÃO ---

    def iniciar_simulacao(self):
        self.parar_simulacao(final_state=False)
        cadeia = self.entrada_cadeia.get()
        tipo = self.tipo_automato.get()

        self.lbl_cadeia_consumida.configure(text="")
        self.lbl_cadeia_restante.configure(text=cadeia if tipo not in ["Turing"] else "", text_color=self.default_fg_color)
        self.lbl_output_valor.configure(text="")
        self.lbl_tape_valor.configure(text="" if tipo == "Turing" else "")

        try:
            if not self.automato.estados: raise ValueError("O autômato está vazio.")
            if not self.automato.estado_inicial:
                if self.automato.estados:
                    first_state_name = next(iter(self.automato.estados))
                    print(f"Aviso: Estado inicial não definido. Usando '{first_state_name}' como inicial.")
                    self.automato.definir_estado_inicial(first_state_name)
                    self.desenhar_automato()
                else: raise ValueError("Estado inicial não definido e autômato vazio.")

            if tipo == "AFD": self.simulador = SimuladorAFD(self.automato, cadeia)
            elif tipo == "AFN": self.simulador = SimuladorAFN(self.automato, cadeia)
            elif tipo == "AP": self.simulador = SimuladorAP(self.automato, cadeia)
            elif tipo == "Moore": self.simulador = SimuladorMoore(self.automato, cadeia)
            elif tipo == "Mealy": self.simulador = SimuladorMealy(self.automato, cadeia)
            elif tipo == "Turing": self.simulador = SimuladorMT(self.automato, cadeia)

        except Exception as e:
            messagebox.showerror("Erro ao Iniciar", str(e)); return

        self.btn_simular.configure(text="⏹ Parar", command=self.parar_simulacao)
        self.btn_proximo_passo.configure(state="normal")
        self.lbl_status_simulacao.configure(text="Simulando...", text_color=self.default_fg_color)
        self.executar_proximo_passo()

    def parar_simulacao(self, final_state=False):
        self.simulador = None
        self.btn_simular.configure(text="▶ Iniciar", command=self.iniciar_simulacao)
        self.btn_proximo_passo.configure(state="disabled")
        if not final_state:
            self.lbl_status_simulacao.configure(text="Status: Aguardando", text_color=self.default_fg_color)
            self.lbl_cadeia_consumida.configure(text="")
            self.lbl_cadeia_restante.configure(text="", text_color=self.default_fg_color)
            self.lbl_output_valor.configure(text="")
            self.lbl_tape_valor.configure(text="")
            self.desenhar_automato()

    def executar_proximo_passo(self):
        if not self.simulador: return
        passo_info = self.simulador.proximo_passo()
        tipo = self.tipo_automato.get()

        if not passo_info:
            current_status_text = self.lbl_status_simulacao.cget("text")
            if current_status_text == "Simulando..." or current_status_text == "Status: Aguardando":
                aceitou = False
                try:
                    last_step_vars = self.simulador.gerador.gi_frame.f_locals
                    last_active_states = last_step_vars.get('estado_atual', last_step_vars.get('estados_atuais', set()))
                    if last_active_states and hasattr(self.simulador, 'automato') and self.simulador.automato.estados_finais:
                        aceitou = any(self.simulador.automato.estados[e] in self.simulador.automato.estados_finais
                                        for e in last_active_states if e in self.simulador.automato.estados)
                except Exception as e:
                    print(f"Erro ao verificar estado final: {e}")

                if aceitou: self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita)
                else: self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita)

            self.parar_simulacao(final_state=True)
            return

        status = passo_info["status"]
        extra_info_canvas = None

        if "tape" in passo_info and passo_info["tape"] is not None:
            self.lbl_tape_valor.configure(text=passo_info["tape"])
            extra_info_canvas = passo_info["tape"]

        if "output" in passo_info and passo_info["output"] is not None:
            self.lbl_output_valor.configure(text=passo_info["output"])

        if "pilha" in passo_info and passo_info["pilha"] is not None:
             extra_info_canvas = passo_info["pilha"]

        if "cadeia_restante" in passo_info and tipo != "Turing":
            cadeia_restante = passo_info['cadeia_restante']
            cadeia_original = self.entrada_cadeia.get()
            split_point = len(cadeia_original) - len(cadeia_restante)
            cadeia_consumida = cadeia_original[:split_point]
            self.lbl_cadeia_consumida.configure(text=cadeia_consumida)
            self.lbl_cadeia_restante.configure(text=cadeia_restante, text_color=self.default_fg_color)
        elif tipo == "Turing":
             self.lbl_cadeia_consumida.configure(text="")
             self.lbl_cadeia_restante.configure(text="")

        if status == "executando":
            self.desenhar_automato(passo_info["estado_atual"], passo_info.get("transicao_ativa"), extra_info_canvas)

        elif status == "aceita":
            self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita)
            if tipo != "Turing": self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get()); self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True)

        elif status == "rejeita":
            self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita)
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True)

        elif status == "finalizado":
            self.lbl_status_simulacao.configure(text="Processamento Concluído", text_color=self.cor_finalizado)
            if tipo != "Turing": self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get()); self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True)

        elif status == "erro":
            messagebox.showerror("Erro", passo_info["mensagem"])
            self.parar_simulacao()

# --- CLASSES DE DIÁLOGO (ATUALIZADAS COM ESTILO) ---

class TransicaoPilhaDialog(ctk.CTkToplevel):
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição AP")
        self.resultado = None
        self.geometry("300x350")
        if style_dict is None: style_dict = {}

        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))

        ctk.CTkLabel(self, text="Entrada (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_entrada = ctk.CTkEntry(self, **style_dict)
        self.e_entrada.pack(padx=20, pady=5)
        self.e_entrada.insert(0, 'e')

        ctk.CTkLabel(self, text="Desempilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_pop = ctk.CTkEntry(self, **style_dict)
        self.e_pop.pack(padx=20, pady=5)
        self.e_pop.insert(0, 'e')

        ctk.CTkLabel(self, text="Empilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_push = ctk.CTkEntry(self, **style_dict)
        self.e_push.pack(padx=20, pady=5)
        self.e_push.insert(0, 'e')

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set()
        self.e_entrada.focus()

    def ok(self):
        self.resultado = {
            'entrada': EPSILON if (ent := self.e_entrada.get()) == 'e' else ent,
            'pop': EPSILON if (pop := self.e_pop.get()) == 'e' else pop,
            'push': EPSILON if (push := self.e_push.get()) == 'e' else push
        }
        self.destroy()

class TransicaoMealyDialog(ctk.CTkToplevel):
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
        self.resultado = {
            'simbolo': (s := self.e_simbolo.get()) if s else 'e',
            'output': (o := self.e_output.get()) if o else 'e'
        }
        self.destroy()

class TransicaoTuringDialog(ctk.CTkToplevel):
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
        self.e_lido.insert(0, 'B')

        ctk.CTkLabel(self, text="Símbolo Escrito:").pack(padx=20, pady=(10,0))
        self.e_escrito = ctk.CTkEntry(self, **style_dict)
        self.e_escrito.pack(padx=20, pady=5)
        self.e_escrito.insert(0, 'B')

        ctk.CTkLabel(self, text="Direção (L/R):").pack(padx=20, pady=(10,0))
        self.e_dir = ctk.CTkEntry(self, width=50, **style_dict)
        self.e_dir.pack(padx=20, pady=5)
        self.e_dir.insert(0, 'R')

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set()
        self.e_lido.focus()

    def ok(self):
        lido = self.e_lido.get() or 'B'
        escrito = self.e_escrito.get() or 'B'
        direcao = (self.e_dir.get() or 'R').upper()
        if direcao not in ['L', 'R']:
            messagebox.showerror("Erro", "Direção deve ser 'L' ou 'R'.", parent=self)
            return
        if len(lido) > 1 or len(escrito) > 1:
             messagebox.showerror("Erro", "Símbolos da fita devem ter apenas 1 caractere.", parent=self)
             return
        self.resultado = {'lido': lido, 'escrito': escrito, 'dir': direcao}
        self.destroy()