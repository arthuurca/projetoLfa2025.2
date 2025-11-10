import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog # Adicionado filedialog
import math
import os # Adicionado os
import xml.etree.ElementTree as ET # Adicionado ET para JFF
from xml.dom import minidom # Adicionado minidom para JFF
from PIL import ImageGrab, Image # Adicionado ImageGrab e Image para JPG
import copy # Importa a biblioteca de cópia

# --- Imports de módulos locais (simulados para o exemplo) ---
# ... (Nenhuma mudança nesta seção de imports) ...
try:
    from automato.automato_finito import AFD, AFN
    from automato.automato_pilha import AutomatoPilha
    from automato.maquinas_moore_mealy import MaquinaMoore, MaquinaMealy
    from automato.maquina_turing import MaquinaTuring
    from automato import EPSILON
    from simulador.simulador_passos import (
        SimuladorAFD, SimuladorAFN, SimuladorAP,
        SimuladorMoore, SimuladorMealy, SimuladorMT
    )
except ImportError:
    print("Aviso: Módulos do autômato não encontrados. Criando classes placeholder.")
    # Classes placeholder para permitir a execução do código
    EPSILON = "ε"
    class BaseAutomato:
        def __init__(self): self.estados = {}; self.transicoes = {}; self.estado_inicial = None; self.estados_finais = set()
        def adicionar_estado(self, nome, x, y, **kwargs): self.estados[nome] = self(nome, **kwargs)
        def definir_estado_inicial(self, nome): self.estado_inicial = nome; self.estados[nome].is_inicial = True
        def alternar_estado_final(self, nome):
            self.estados[nome].is_final = not self.estados[nome].is_final
            if self.estados[nome].is_final: self.estados_finais.add(nome)
            else: self.estados_finais.discard(nome)
        def adicionar_estado_final(self, nome):
            if nome in self.estados:
                self.estados[nome].is_final = True
                self.estados_finais.add(nome)
        def deletar_estado(self, nome): self.estados.pop(nome, None)
        def deletar_transicoes_entre(self, o, d): pass # Simulado: A lógica real estaria no backend
        def adicionar_transicao(self, *args, **kwargs): pass # Simulado
        def renomear_estado(self, antigo, novo):
            if novo in self.estados: raise ValueError("Estado já existe")
            self.estados[novo] = self.estados.pop(antigo)
            self.estados[novo].nome = novo
        def set_output_estado(self, nome, output): self.estados[nome].output = output
        def __call__(self, nome, **kwargs):
            s = type(f"Estado{nome}", (object,), {"nome": nome, "is_inicial": False, "is_final": False, "output": ""})()
            for k, v in kwargs.items(): setattr(s, k, v)
            return s
    class AFD(BaseAutomato): pass
    class AFN(BaseAutomato): pass
    class AutomatoPilha(BaseAutomato): pass
    class MaquinaMoore(BaseAutomato): pass
    class MaquinaMealy(BaseAutomato): pass
    class MaquinaTuring(BaseAutomato): simbolo_branco = '☐'
    class BaseSimulador:
        def __init__(self, automato, cadeia): self.automato = automato; self.cadeia = cadeia; self.passos = iter([])
        def proximo_passo(self): return next(self.passos, None)
    class SimuladorAFD(BaseSimulador): pass
    class SimuladorAFN(BaseSimulador): pass
    class SimuladorAP(BaseSimulador): pass
    class SimuladorMoore(BaseSimulador): pass
    class SimuladorMealy(BaseSimulador): pass
    class SimuladorMT(BaseSimulador): pass
# --- Fim dos imports simulados ---


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
        
        # --- NOVAS VARIÁVEIS DE ZOOM ---
        self.zoom_level = 1.5 # Modificado: Inicia em 150%

        # --- Cores e Estilos ... (Nenhuma mudança nesta seção) ...
        self.default_fg_color = (ctk.ThemeManager.theme["CTkLabel"]["text_color"][0], ctk.ThemeManager.theme["CTkLabel"]["text_color"][1])
        self.app_bg_color = ("gray85", "gray20")
        self.cor_verde_fg = ("#4CAF50", "#388E3C")
        self.cor_verde_hover = ("#388E3C", "#2E7D32")
        self.cor_azul_fg = ("#2196F3", "#1976D2")
        self.cor_azul_hover = ("#1976D2", "#1565C0")
        self.cor_vermelha_fg = ("#d32f2f", "#d32f2f") # Tupla para consistência
        self.cor_vermelha_hover = ("#b71c1c", "#b71c1c") # Tupla para consistência
        self.cor_cinza_fg = ("#565b5e", "#565b5e")
        self.cor_cinza_hover = ("#4a4f52", "#4a4f52")
        self.cor_consumida = self.cor_verde_fg
        self.cor_aceita = self.cor_verde_fg
        self.cor_rejeita = self.cor_vermelha_fg
        self.cor_finalizado = self.cor_azul_fg 
        self.canvas_bg = ("#FFFFFF", "#2B2B2B") # Canvas branco (light) / cinza escuro (dark)
        self.canvas_fg_color = ("black", "white") # Cor da linha da transição
        self.canvas_estado_fill = ("white", "#343638")
        self.canvas_estado_text = ("black", "white")
        self.canvas_transicao_text = self.cor_azul_fg # Texto da transição azul
        self.canvas_transicao_ativa = self.cor_verde_fg
        self.canvas_estado_ativo = self.cor_vermelha_fg # Estado ativo na simulação
        self.cor_selecao_grupo = self.cor_azul_fg # Estado selecionado no modo Mover
        self.cor_destrutiva_fg = self.cor_vermelha_fg
        self.cor_destrutiva_hover = self.cor_vermelha_hover
        self.cor_navegacao_fg = self.cor_cinza_fg 
        self.cor_navegacao_hover = self.cor_cinza_hover
        self.cor_ferramenta_fg = self.cor_azul_fg # Ferramentas agora são azuis
        self.cor_ferramenta_hover = self.cor_azul_hover
        self.cor_simulacao_fg = self.cor_verde_fg # Botões de simulação são verdes
        self.cor_simulacao_hover = self.cor_verde_hover
        self.style_font_bold = ctk.CTkFont(size=12, weight="bold")
        self.style_top_widget = { "corner_radius": 10 }
        self.style_tool_button = { "corner_radius": 10, "font": self.style_font_bold, "border_spacing": 5 }
        self.style_sim_button = { "corner_radius": 10, "font": self.style_font_bold }
        self.style_dialog_widget = { "corner_radius": 10 }

        # --- Variáveis de Estado da UI ---
        self.current_mode = "MOVER"
        self.tool_buttons = {}
        self.origem_transicao = None
        self.estado_movendo = None
        self.simulador = None

        # --- NOVAS VARIÁVEIS PARA SELEÇÃO MÚLTIPLA ---
        self.selection_box_start = None
        self.selection_box_id = None    
        self.selection_group = set()    
        self.drag_start_pos = None

        # --- NOVO: Variáveis do Histórico Undo/Redo ---
        self.history_undo_stack = []
        self.history_redo_stack = []
        self.btn_undo = None
        self.btn_redo = None

        # --- Layout Principal ---
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(2, weight=1) # Modificado: Aponta para o canvas_frame
        self.master.grid_rowconfigure(3, weight=0)
        self.master.grid_rowconfigure(4, weight=0)

        # --- 1. Barra Superior ---
        top_bar = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
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

        # --- NOVO: Botões Undo/Redo ---
        self.btn_undo = ctk.CTkButton(top_bar, text="↩ Voltar (Undo)",
                                    command=self.undo_action,
                                    width=120,
                                    fg_color=self.cor_ferramenta_fg,
                                    hover_color=self.cor_ferramenta_hover,
                                    **self.style_top_widget)
        self.btn_undo.pack(side="left", padx=5)

        self.btn_redo = ctk.CTkButton(top_bar, text="↪ Ir (Redo)",
                                    command=self.redo_action,
                                    width=100,
                                    fg_color=self.cor_ferramenta_fg,
                                    hover_color=self.cor_ferramenta_hover,
                                    **self.style_top_widget)
        self.btn_redo.pack(side="left", padx=5)
        # --- FIM NOVO ---

        self.btn_theme_toggle = ctk.CTkButton(top_bar, text="",
                                            command=self.toggle_theme, width=120,
                                            **self.style_top_widget)
        self.btn_theme_toggle.pack(side="left", padx=10)
        
        self.btn_open_jff = ctk.CTkButton(top_bar, text="📂 Abrir JFF",
                                            command=self.importar_de_jff, width=120,
                                            fg_color=self.cor_ferramenta_fg, # Azul
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_open_jff.pack(side="left", padx=(20, 5))

        self.btn_export_jff = ctk.CTkButton(top_bar, text="💾 Salvar JFF",
                                            command=self.exportar_para_jff, width=120,
                                            fg_color=self.cor_ferramenta_fg, # Azul
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_export_jff.pack(side="left", padx=(5, 5)) # Padding ajustado

        self.btn_export_jpg = ctk.CTkButton(top_bar, text="🖼️ Salvar JPG",
                                            command=self.exportar_para_jpg, width=120,
                                            fg_color=self.cor_ferramenta_fg, # Azul
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_export_jpg.pack(side="left", padx=5)


        if self.voltar_menu_callback:
            self.btn_voltar = ctk.CTkButton(
            top_bar,
            text="← Voltar ao Menu",
            command=self.voltar_ao_menu,
            width=140,
            fg_color=self.cor_navegacao_fg, # Cinza
            hover_color=self.cor_navegacao_hover,
            **self.style_top_widget
        )
        self.btn_voltar.pack(side="right", padx=(10, 10))

        # --- 2. Barra de Ferramentas ... (Nenhuma mudança nesta seção) ...
        tool_bar_container = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
        tool_bar_container.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        tool_bar = ctk.CTkFrame(tool_bar_container, fg_color="transparent") # MUDANÇA: Transparente
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


        # --- 3. Canvas e Slider de Zoom ... (Nenhuma mudança nesta seção) ...
        canvas_frame = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
        canvas_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=0) # Coluna do Slider
        canvas_frame.grid_columnconfigure(1, weight=1) # Coluna do Canvas
        self.zoom_slider = ctk.CTkSlider(
            canvas_frame,
            from_=0.2,
            to=3.0,
            number_of_steps=28,
            orientation="vertical",
            command=self.on_zoom_change,
            button_color=self.cor_ferramenta_fg,     # Cor do botão (Azul)
            button_hover_color=self.cor_ferramenta_hover
        )
        self.zoom_slider.grid(row=0, column=0, sticky="ns", padx=(0, 5))
        self.zoom_slider.set(1.5) # Modificado: Define o zoom inicial como 150%
        self.canvas = tk.Canvas(canvas_frame, bg=self.canvas_bg[0], bd=0, highlightthickness=0) # MUDANÇA: Cor do canvas
        self.canvas.grid(row=0, column=1, sticky="nsew") 


        # --- 4. Frame Fita/Saída ... (Nenhuma mudança nesta seção) ...
        self.frame_extra_info = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
        self.frame_extra_info.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.frame_extra_info.grid_columnconfigure(1, weight=1)
        self.lbl_output_tag = ctk.CTkLabel(self.frame_extra_info, text="Saída:", font=ctk.CTkFont(weight="bold"))
        self.lbl_output_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.cor_finalizado)
        self.lbl_tape_tag = ctk.CTkLabel(self.frame_extra_info, text="Fita:", font=ctk.CTkFont(weight="bold"))
        self.lbl_tape_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(family="Courier New", size=16, weight="bold"))

        # --- 5. Barra Inferior (Simulação) ... (Nenhuma mudança nesta seção) ...
        frame_simulacao = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
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
                                    fg_color=self.cor_simulacao_fg, # MUDANÇA: Verde
                                    hover_color=self.cor_simulacao_hover,
                                    **self.style_sim_button)
        self.btn_simular.grid(row=0, column=2, padx=5, pady=10)
        self.btn_proximo_passo = ctk.CTkButton(frame_simulacao, text="Passo >",
                                            command=self.executar_proximo_passo, width=100,
                                            fg_color=self.cor_simulacao_fg, # MUDANÇA: Verde
                                            hover_color=self.cor_simulacao_hover,
                                            **self.style_sim_button)
        self.btn_proximo_passo.grid(row=0, column=3, padx=5, pady=10)
        cadeia_status_frame = ctk.CTkFrame(frame_simulacao, fg_color="transparent") # MUDANÇA: Transparente
        cadeia_status_frame.grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.lbl_cadeia_consumida = ctk.CTkLabel(cadeia_status_frame, text="", text_color=self.cor_consumida, font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_cadeia_consumida.pack(side="left")
        self.lbl_cadeia_restante = ctk.CTkLabel(cadeia_status_frame, text="", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_cadeia_restante.pack(side="left")
        self.lbl_status_simulacao = ctk.CTkLabel(frame_simulacao, text="Status: Aguardando", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_status_simulacao.grid(row=0, column=5, padx=10, pady=10, sticky="e")


        # --- Bindings e Inicialização ---
        self.canvas.bind("<Button-1>", self.clique_canvas)
        self.canvas.bind("<Double-Button-1>", self.duplo_clique_canvas)
        self.canvas.bind("<B1-Motion>", self.arrastar_canvas)
        self.canvas.bind("<ButtonRelease-1>", self.soltar_canvas)

        self.mudar_tipo_automato(save_history=False) # <--- MODIFICADO
        self.set_active_mode("MOVER")
        self.btn_proximo_passo.configure(state="disabled")
        self._atualizar_widgets_extra_info()

        self.sync_theme()
        
        # --- NOVO: Salva o estado inicial e atualiza botões ---
        self._save_history_state()
        self._update_history_buttons()


    # --- NOVO: Funções de Histórico (Undo/Redo) ---

    def _save_history_state(self):
        """Salva o estado atual no histórico e limpa o 'redo'."""
        # Cria um snapshot profundo do estado atual
        snapshot = (copy.deepcopy(self.automato), copy.deepcopy(self.positions))
        self.history_undo_stack.append(snapshot)
        # Qualquer nova ação limpa o stack de "refazer"
        self.history_redo_stack.clear()
        # Atualiza o estado dos botões
        self._update_history_buttons()

    def _load_history_state(self, state_snapshot):
        """Carrega um estado do histórico."""
        # Carrega o snapshot
        self.automato, self.positions = copy.deepcopy(state_snapshot) # Copia para evitar referência
        self.parar_simulacao(final_state=False) # Garante que a simulação pare
        self.desenhar_automato()
        self._update_history_buttons()

    def undo_action(self):
        """Desfaz a última ação."""
        if not self.history_undo_stack:
            return
        
        # Salva o estado ATUAL para o stack de 'redo'
        current_snapshot = (copy.deepcopy(self.automato), copy.deepcopy(self.positions))
        self.history_redo_stack.append(current_snapshot)
        
        # Remove e carrega o estado anterior do stack 'undo'
        previous_snapshot = self.history_undo_stack.pop()
        self._load_history_state(previous_snapshot)

    def redo_action(self):
        """Refaz a última ação desfeita."""
        if not self.history_redo_stack:
            return
            
        # Salva o estado ATUAL de volta para o stack 'undo'
        current_snapshot = (copy.deepcopy(self.automato), copy.deepcopy(self.positions))
        self.history_undo_stack.append(current_snapshot)
        
        # Remove e carrega o próximo estado (que foi desfeito)
        next_snapshot = self.history_redo_stack.pop()
        self._load_history_state(next_snapshot)

    def _update_history_buttons(self):
        """Ativa/desativa os botões de undo/redo."""
        if self.btn_undo:
            self.btn_undo.configure(state="normal" if self.history_undo_stack else "disabled")
        if self.btn_redo:
            self.btn_redo.configure(state="normal" if self.history_redo_stack else "disabled")

    # --- FIM DAS FUNÇÕES DE HISTÓRICO ---


    # --- NOVAS FUNÇÕES DE ZOOM ... (Nenhuma mudança nesta seção) ...
    def on_zoom_change(self, value):
        self.zoom_level = float(value)
        self.desenhar_automato()
    def _logical_to_view(self, x, y):
        view_x = x * self.zoom_level
        view_y = y * self.zoom_level
        return view_x, view_y
    def _view_to_logical(self, x, y):
        if self.zoom_level == 0: return x, y
        logical_x = x / self.zoom_level
        logical_y = y / self.zoom_level
        return logical_x, logical_y

    # --- FUNÇÕES DE CONTROLE DE MODO ... (Nenhuma mudança nesta seção) ...
    def set_active_mode(self, mode_id):
        if mode_id == self.current_mode: self.current_mode = "MOVER" # Desativa ao clicar novamente
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
        self.master.config(cursor=cursor_map.get(mode, "arrow")) # Usa 'arrow' como padrão
        self.origem_transicao = None 
        
    # --- FUNÇÕES DE TEMA ... (Nenhuma mudança nesta seção) ...
    def sync_theme(self):
        current_mode = ctk.get_appearance_mode()
        current_theme_index = 0 if current_mode == "Light" else 1
        self.update_theme_button_text() # Atualiza o texto do botão de tema
        self.default_fg_color = (ctk.ThemeManager.theme["CTkLabel"]["text_color"][0], ctk.ThemeManager.theme["CTkLabel"]["text_color"][1])
        self.update_button_styles()
        self.canvas.configure(bg=self.canvas_bg[current_theme_index])
        self.desenhar_automato()
    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.sync_theme()
    def voltar_ao_menu(self):
        if self.voltar_menu_callback:
            if self.simulador:
                self.parar_simulacao() # Para a simulação se estiver ativa
            for widget in self.master.winfo_children():
                widget.destroy()
            self.voltar_menu_callback() # Chama a função que recria o menu
    def update_theme_button_text(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            button_text = "☀️Modo Claro"; btn_fg_color = "#F0F0F0"; btn_hover_color = "#D5D5D5"; btn_text_color = "#1A1A1A"
        else:
            button_text = "🌙Modo Escuro"; btn_fg_color = "#333333"; btn_hover_color = "#4A4A4A"; btn_text_color = "#E0E0E0"
        self.btn_theme_toggle.configure(text=button_text, fg_color=btn_fg_color, hover_color=btn_hover_color, text_color=btn_text_color)


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

    def mudar_tipo_automato(self, event=None, save_history=True):
        """
        Chamado quando o tipo de autômato é alterado no ComboBox.
        MODIFICADO: Reseta o histórico.
        """
        self.limpar_tela(save_current_state=save_history, reset_history=True) # <--- MODIFICADO
        self._atualizar_widgets_extra_info() # Atualiza os widgets extras

    def limpar_tela(self, save_current_state=True, reset_history=False):
        """
        Reseta o autômato, posições e estado da simulação.
        MODIFICADO: Salva o estado antes de limpar (para undo) ou reseta o histórico.
        """
        if save_current_state:
            self._save_history_state()

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
        self.selection_group.clear() # Limpa seleção
        self.parar_simulacao(final_state=False) # Para e reseta a simulação
        self.set_active_mode("MOVER") # Volta para o modo padrão
        
        # --- NOVO: Reseta o histórico se solicitado ---
        if reset_history:
            self.history_undo_stack = []
            self.history_redo_stack = []
            self._save_history_state() # Salva o estado em branco como o novo estado inicial
        
        self.desenhar_automato() # Limpa e redesenha o canvas
        self._atualizar_widgets_extra_info() # Atualiza widgets extras
        self._update_history_buttons() # Atualiza botões


    # --- AÇÕES DO CANVAS (MODIFICADAS PARA ZOOM E SELEÇÃO MÚLTIPLA) ---
    def clique_canvas(self, event):
        """Processa um clique no canvas de acordo com o modo ativo."""
        mode = self.current_mode
        
        logical_x, logical_y = self._view_to_logical(event.x, event.y)
        estado_clicado = self._get_estado_em(logical_x, logical_y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y) 

        # --- LÓGICA DO MODO MOVER (SELEÇÃO E GRUPO) ---
        if mode == "MOVER":
            if estado_clicado:
                if estado_clicado.nome not in self.selection_group:
                    self.selection_group.clear()
                    self.selection_group.add(estado_clicado.nome)
                self.estado_movendo = estado_clicado # Indica que o drag começou *sobre* um estado
                self.drag_start_pos = (event.x, event.y) # Armazena início do drag
            elif not estado_clicado and not transicao_clicada: # Clicou no vazio
                self.estado_movendo = None
                self.selection_group.clear() # Limpa seleção anterior
                self.selection_box_start = (event.x, event.y) # Inicia o box-select
                self.drag_start_pos = (event.x, event.y) # Armazena início do drag
                if self.selection_box_id: self.canvas.delete(self.selection_box_id)
                self.selection_box_id = self.canvas.create_rectangle(
                    event.x, event.y, event.x, event.y, 
                    fill="#007acc", stipple="gray25", outline="#007acc"
                )
            self.desenhar_automato() 
            return 

        # --- OUTROS MODOS ---
        self.selection_group.clear() 

        if mode == "ESTADO" and not estado_clicado and not transicao_clicada:
            self._save_history_state() # <--- NOVO: Salva antes de adicionar
            nome_estado = f"q{self.contador_estados}"
            while nome_estado in self.automato.estados:
                self.contador_estados += 1; nome_estado = f"q{self.contador_estados}"
            if self.tipo_automato.get() == "Moore":
                dialog = ctk.CTkInputDialog(text="Símbolo de Saída do Estado (vazio=default):", title="Criar Estado Moore")
                output = dialog.get_input()
                if output is None: 
                    self.undo_action() # <--- NOVO: Desfaz o save se o usuário cancelar
                    return
                self.automato.adicionar_estado(nome_estado, logical_x, logical_y, output=output)
            else:
                self.automato.adicionar_estado(nome_estado, logical_x, logical_y)
            self.positions[nome_estado] = (logical_x, logical_y) 
            self.contador_estados += 1
            
        elif estado_clicado:
            if mode == "TRANSICAO":
                if not self.origem_transicao:
                    self.origem_transicao = estado_clicado
                else:
                    self._criar_transicao(self.origem_transicao, estado_clicado)
                    self.origem_transicao = None
            elif mode == "INICIAL": 
                self._save_history_state() # <--- NOVO
                self.automato.definir_estado_inicial(estado_clicado.nome)
            elif mode == "FINAL": 
                self._save_history_state() # <--- NOVO
                self.automato.alternar_estado_final(estado_clicado.nome)
            elif mode == "DELETAR":
                self._save_history_state() # <--- NOVO
                nome_a_deletar = estado_clicado.nome
                self.automato.deletar_estado(nome_a_deletar)
                self.positions.pop(nome_a_deletar, None)
                
        elif transicao_clicada and mode == "DELETAR":
            self._save_history_state() # <--- NOVO
            origem, destino = transicao_clicada
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            else:
                print(f"Aviso: Método 'deletar_transicoes_entre' não implementado para {type(self.automato)}")
        
        elif not estado_clicado and not transicao_clicada:
            self.origem_transicao = None

        self.desenhar_automato() # Redesenha o autômato

    def duplo_clique_canvas(self, event):
        """Processa um duplo clique no canvas (renomear estado ou editar transição no modo MOVER)."""
        mode = self.current_mode

        logical_x, logical_y = self._view_to_logical(event.x, event.y)
        estado_clicado = self._get_estado_em(logical_x, logical_y)
        transicao_clicada = self._get_transicao_label_em(event.x, event.y)

        # Se deu duplo clique num estado no modo MOVER: renomeia
        if estado_clicado and mode == "MOVER":
            self._save_history_state() # <--- NOVO: Salva antes de qualquer edição
            novo_nome = ctk.CTkInputDialog(text="Digite o novo nome do estado:", title="Renomear Estado").get_input()
            
            nome_mudou = False
            output_mudou = False

            if self.tipo_automato.get() == "Moore":
                novo_output = ctk.CTkInputDialog(text="Digite a nova saída do estado:", title="Editar Saída Moore").get_input()
                if novo_output is not None:
                    self.automato.set_output_estado(estado_clicado.nome, novo_output)
                    output_mudou = True

            if novo_nome and novo_nome != estado_clicado.nome:
                try:
                    pos = self.positions.pop(estado_clicado.nome)
                    self.automato.renomear_estado(estado_clicado.nome, novo_nome)
                    self.positions[novo_nome] = pos
                    nome_mudou = True
                except ValueError as e:
                    messagebox.showerror("Erro ao Renomear", str(e))
                    if estado_clicado.nome in self.automato.estados: self.positions[estado_clicado.nome] = pos
            
            if not nome_mudou and not output_mudou:
                self.undo_action() # <--- NOVO: Desfaz o save se nada mudou
            
            self.desenhar_automato()
        
        elif transicao_clicada and mode == "MOVER":
            # --- LÓGICA DE EDIÇÃO DE TRANSIÇÃO MODIFICADA ---
            origem, destino = transicao_clicada
            tipo = self.tipo_automato.get()

            if tipo in ["AFD", "AFN", "Moore"]:
                # Comportamento antigo: edita o *grupo* de transições
                self._editar_label_transicao(origem, destino)
            else:
                # Comportamento novo: seleciona e edita uma transição complexa (AP, Mealy, Turing)
                self._editar_transicao_complexa(origem, destino)


    def arrastar_canvas(self, event):
        """Move o estado selecionado ou o grupo de seleção."""
        if self.current_mode != "MOVER" or not self.drag_start_pos:
            return 

        delta_x = event.x - self.drag_start_pos[0]
        delta_y = event.y - self.drag_start_pos[1]
        logical_delta_x = delta_x / self.zoom_level
        logical_delta_y = delta_y / self.zoom_level

        if self.selection_box_start:
            start_x, start_y = self.selection_box_start
            self.canvas.coords(self.selection_box_id, start_x, start_y, event.x, event.y)
            log_start_x, log_start_y = self._view_to_logical(start_x, start_y)
            log_end_x, log_end_y = self._view_to_logical(event.x, event.y)
            log_box_x1 = min(log_start_x, log_end_x); log_box_y1 = min(log_start_y, log_end_y)
            log_box_x2 = max(log_start_x, log_end_x); log_box_y2 = max(log_start_y, log_end_y)
            self.selection_group.clear()
            for nome, (sx, sy) in self.positions.items():
                if (log_box_x1 <= sx <= log_box_x2) and (log_box_y1 <= sy <= log_box_y2):
                    self.selection_group.add(nome)
        
        # Move *todos* os estados no grupo de seleção
        for nome in self.selection_group:
            if nome in self.positions:
                old_log_x, old_log_y = self.positions[nome]
                self.positions[nome] = (old_log_x + logical_delta_x, old_log_y + logical_delta_y)

        self.drag_start_pos = (event.x, event.y)
        self.desenhar_automato() 

    def soltar_canvas(self, event):
        """
        Finaliza o arraste do estado ou da seleção.
        MODIFICADO: Salva o estado no histórico *após* mover.
        """
        # --- NOVO: Verifica se uma ação de movimento ocorreu ---
        movimento_ocorrreu = self.estado_movendo is not None or self.selection_box_start is not None

        # Reseta os estados de drag/seleção
        self.estado_movendo = None
        self.drag_start_pos = None
        self.selection_box_start = None # Importante
        
        if self.selection_box_id:
            self.canvas.delete(self.selection_box_id)
            self.selection_box_id = None
        
        # --- NOVO: Salva o estado APÓS o movimento ---
        if movimento_ocorrreu:
            self._save_history_state()
        
        self.desenhar_automato() # Redesenha no estado final

    # --- INÍCIO DA FUNÇÃO CORRIGIDA (USA NOVO DIÁLOGO) ---
    def _editar_label_transicao(self, origem, destino):
        """Abre um diálogo para editar os símbolos de uma transição (AFD, AFN, Moore)."""
        tipo = self.tipo_automato.get()
        if tipo in ["AP", "Mealy", "Turing"]:
            self._editar_transicao_complexa(origem, destino)
            return

        # 1. Encontra os símbolos atuais
        simbolos_atuais = set()
        agrupado = self._agrupar_transicoes()
        if origem in agrupado and destino in agrupado[origem]:
            simbolos_brutos = set()
            if tipo in ["AFD", "AFN", "Moore"]:
                for (o, s), dests in self.automato.transicoes.items():
                    dests_set = dests if isinstance(dests, set) else {dests}
                    if o == origem and destino in dests_set:
                        simbolos_brutos.add(s)
            simbolos_atuais = {s.replace(EPSILON, "e") for s in simbolos_brutos}
        label_atual = ",".join(sorted(list(simbolos_atuais)))

        # 2. Cria o *novo* diálogo personalizado
        dialog = TransicaoSimplesDialog(self.master, origem, destino, self.style_dialog_widget)
        
        # 3. Pré-preenche o campo (AGORA SEGURO)
        dialog.e_simbolos.insert(0, label_atual)
        
        # 4. Espera o diálogo
        self.master.wait_window(dialog)
        simbolo_input = dialog.resultado # Pega o resultado do novo diálogo

        # 5. Processa o resultado (lógica idêntica à anterior)
        if simbolo_input is not None and simbolo_input != label_atual:
            self._save_history_state() # Salva o estado anterior
            
            # Deleta todas as transições entre os dois nós
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem, destino)
            else:
                print(f"Aviso: 'deletar_transicoes_entre' não implementado em {type(self.automato)}")

            # Adiciona as novas transições
            novos_simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
            for s in novos_simbolos:
                simbolo_final = EPSILON if s == 'e' or s == '' else s # Usa EPSILON para 'e' ou vazio
                self.automato.adicionar_transicao(origem, simbolo_final, destino)
                
            self.desenhar_automato()
        elif simbolo_input is None:
            pass # Usuário cancelou
    # --- FIM DA FUNÇÃO CORRIGIDA ---


    # --- Funções para editar transições complexas ---
    
    def _find_transitions_between(self, origem_nome, destino_nome):
        """Encontra todas as transições individuais entre dois estados."""
        transicoes_encontradas = []
        tipo = self.tipo_automato.get()
        trans_dict = self.automato.transicoes

        if tipo == "AP":
            for (o, s_in, s_pop), destinos_set in trans_dict.items():
                if o == origem_nome and destinos_set:
                    for dest, s_push in destinos_set:
                        if dest == destino_nome:
                            label = f"{s_in.replace(EPSILON,'e')},{s_pop.replace(EPSILON,'e')};{s_push.replace(EPSILON,'e')}"
                            transicoes_encontradas.append({"tipo": "AP", "entrada": s_in, "pop": s_pop, "push": s_push, "label": label})
        
        elif tipo == "Mealy":
            for (o, s_in), (dest, s_out) in trans_dict.items():
                if o == origem_nome and dest == destino_nome:
                    label = f"{s_in.replace(EPSILON,'e')} ; {s_out.replace(EPSILON,'e')}"
                    transicoes_encontradas.append({"tipo": "Mealy", "simbolo": s_in, "output": s_out, "label": label})
        
        elif tipo == "Turing":
            simbolo_branco_auto = getattr(self.automato, 'simbolo_branco', '☐')
            for (o, s_read), (dest, s_write, s_dir) in trans_dict.items():
                if o == origem_nome and dest == destino_nome:
                    read_char = simbolo_branco_auto if s_read == simbolo_branco_auto else s_read
                    write_char = simbolo_branco_auto if s_write == simbolo_branco_auto else s_write
                    label = f"{read_char} ; {write_char} , {s_dir}"
                    transicoes_encontradas.append({"tipo": "Turing", "lido": s_read, "escrito": s_write, "dir": s_dir, "label": label})
        
        return transicoes_encontradas

    def _adicionar_transicao_via_dict(self, origem_nome, destino_nome, trans_dict, tipo_override=None):
        """Helper para adicionar uma transição ao autômato a partir de um dicionário."""
        tipo = tipo_override or trans_dict.get('tipo')
        if not tipo: return

        try:
            if tipo == "AP":
                s_in = trans_dict.get('entrada')
                s_pop = trans_dict.get('pop')
                s_push = trans_dict.get('push')
                # A lógica de conversão real acontece aqui, pegando 'e' ou EPSILON do diálogo
                in_final = EPSILON if s_in == 'e' or s_in == EPSILON else s_in
                pop_final = EPSILON if s_pop == 'e' or s_pop == EPSILON else s_pop
                push_final = EPSILON if s_push == 'e' or s_push == EPSILON else s_push
                self.automato.adicionar_transicao(origem_nome, in_final, pop_final, destino_nome, push_final)
            
            elif tipo == "Mealy":
                simbolo = trans_dict.get('simbolo')
                output = trans_dict.get('output')
                simbolo_final = EPSILON if simbolo == 'e' or simbolo == EPSILON else simbolo
                output_final = EPSILON if output == 'e' or output == EPSILON else output
                self.automato.adicionar_transicao(origem_nome, simbolo_final, destino_nome, output_final)

            elif tipo == "Turing":
                lido = trans_dict.get('lido')
                escrito = trans_dict.get('escrito')
                direcao = trans_dict.get('dir')
                self.automato.adicionar_transicao(origem_nome, lido, destino_nome, escrito, direcao)
        
        except Exception as e:
            print(f"Erro ao re-adicionar transição: {e}")
            messagebox.showerror("Erro de Edição", f"Não foi possível re-adicionar a transição: {e}", parent=self.master)


    def _editar_transicao_complexa(self, origem_nome, destino_nome):
        """Abre um seletor e, em seguida, um editor para transições AP, Mealy ou Turing."""
        tipo = self.tipo_automato.get()
        transicoes_encontradas = self._find_transitions_between(origem_nome, destino_nome)
        
        if not transicoes_encontradas:
            return # Nenhuma transição encontrada

        trans_selecionada = None
        index_selecionado = -1

        if len(transicoes_encontradas) == 1:
            # Se só há uma, seleciona ela automaticamente
            trans_selecionada = transicoes_encontradas[0]
            index_selecionado = 0
        else:
            # Se há várias, mostra o diálogo de seleção
            labels = [t['label'] for t in transicoes_encontradas]
            dlg_select = TransicaoSelectorDialog(
                self.master, 
                origem_nome, 
                destino_nome, 
                labels, 
                self.style_dialog_widget
            )
            self.master.wait_window(dlg_select)
            
            if dlg_select.resultado_index is None:
                return # Usuário cancelou a seleção
            
            index_selecionado = dlg_select.resultado_index
            trans_selecionada = transicoes_encontradas[index_selecionado]

        # --- Abrir o diálogo de edição específico, pré-preenchido ---
        dlg_edit = None
        
        if tipo == "AP":
            dlg_edit = TransicaoPilhaDialog(self.master, origem_nome, destino_nome, self.style_dialog_widget)
            dlg_edit.e_entrada.delete(0, 'end'); dlg_edit.e_entrada.insert(0, trans_selecionada['entrada'].replace(EPSILON, 'e'))
            dlg_edit.e_pop.delete(0, 'end'); dlg_edit.e_pop.insert(0, trans_selecionada['pop'].replace(EPSILON, 'e'))
            dlg_edit.e_push.delete(0, 'end'); dlg_edit.e_push.insert(0, trans_selecionada['push'].replace(EPSILON, 'e'))

        elif tipo == "Mealy":
            dlg_edit = TransicaoMealyDialog(self.master, origem_nome, destino_nome, self.style_dialog_widget)
            dlg_edit.e_simbolo.delete(0, 'end'); dlg_edit.e_simbolo.insert(0, trans_selecionada['simbolo'].replace(EPSILON, 'e'))
            dlg_edit.e_output.delete(0, 'end'); dlg_edit.e_output.insert(0, trans_selecionada['output'].replace(EPSILON, 'e'))

        elif tipo == "Turing":
            dlg_edit = TransicaoTuringDialog(self.master, origem_nome, destino_nome, self.style_dialog_widget)
            dlg_edit.e_lido.delete(0, 'end'); dlg_edit.e_lido.insert(0, trans_selecionada['lido'])
            dlg_edit.e_escrito.delete(0, 'end'); dlg_edit.e_escrito.insert(0, trans_selecionada['escrito'])
            dlg_edit.e_dir.delete(0, 'end'); dlg_edit.e_dir.insert(0, trans_selecionada['dir'])

        if not dlg_edit:
            return

        self.master.wait_window(dlg_edit)
        novo_resultado = dlg_edit.resultado

        if novo_resultado:
            # Usuário confirmou a edição
            self._save_history_state() # Salva o estado ANTES da modificação

            # Pega a lista de todas as transições, *exceto* a que foi editada
            outras_transicoes = [t for i, t in enumerate(transicoes_encontradas) if i != index_selecionado]
            
            # Deleta todas as transições entre os dois nós
            if hasattr(self.automato, 'deletar_transicoes_entre'):
                self.automato.deletar_transicoes_entre(origem_nome, destino_nome)
            
            # Re-adiciona as que não foram editadas
            for trans in outras_transicoes:
                self._adicionar_transicao_via_dict(origem_nome, destino_nome, trans)
            
            # Adiciona a nova transição (editada)
            self._adicionar_transicao_via_dict(origem_nome, destino_nome, novo_resultado, tipo_override=tipo)
            
            self.desenhar_automato()
        else:
            # Usuário cancelou a edição, não faz nada
            pass
            
    # --- FIM DAS FUNÇÕES DE EDIÇÃO ---

    def _criar_transicao(self, origem, destino):
        """Abre o diálogo apropriado para criar uma transição entre dois estados."""
        tipo = self.tipo_automato.get()

        if tipo in ["AFD", "AFN", "Moore"]:
            # A criação ainda pode usar o CTkInputDialog, pois não precisa pré-preencher
            dialog = ctk.CTkInputDialog(text="Símbolo(s) (use 'e' para ε, vírgula para separar):", title=f"Criar Transição {tipo}")
            simbolo_input = dialog.get_input()
            if simbolo_input is not None:
                self._save_history_state() # <--- NOVO
                simbolos = [s.strip() for s in simbolo_input.split(',') if s.strip()]
                for s in simbolos:
                    simbolo_final = EPSILON if s == 'e' or s == '' else s
                    self.automato.adicionar_transicao(origem.nome, simbolo_final, destino.nome)

        elif tipo == "AP":
            dlg = TransicaoPilhaDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self._save_history_state() # <--- NOVO
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['entrada'], dlg.resultado['pop'], destino.nome, dlg.resultado['push'])

        elif tipo == "Mealy":
            dlg = TransicaoMealyDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self._save_history_state() # <--- NOVO
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['simbolo'], destino.nome, dlg.resultado['output'])

        elif tipo == "Turing":
            dlg = TransicaoTuringDialog(self.master, origem.nome, destino.nome, self.style_dialog_widget)
            self.master.wait_window(dlg)
            if dlg.resultado:
                self._save_history_state() # <--- NOVO
                self.automato.adicionar_transicao(origem.nome, dlg.resultado['lido'], destino.nome, dlg.resultado['escrito'], dlg.resultado['dir'])

        self.desenhar_automato()


    def _get_estado_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão dentro de algum estado desenhado.
           NOTA: Recebe coordenadas LÓGICAS."""
        for nome, (sx, sy) in self.positions.items():
            if (sx - x)**2 + (sy - y)**2 <= (STATE_RADIUS + 2)**2: 
                if nome in self.automato.estados: return self.automato.estados[nome]
        return None

    def _get_transicao_label_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão sobre alguma label de transição.
           NOTA: Recebe coordenadas VISUAIS (event.x, event.y)."""
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item_id in reversed(items):
            tags = self.canvas.gettags(item_id)
            if "transition_label_text" in tags: 
                for tag in tags:
                    if tag.startswith("label_"):
                        parts = tag.split('_')
                        if len(parts) == 3: return parts[1], parts[2] # Retorna (origem, destino)
        return None

    # --- FUNÇÕES DE DESENHO ... (Nenhuma mudança nesta seção) ...
    def desenhar_automato(self, estados_ativos=None, transicoes_ativas=None, extra_info_str=None):
            try:
                self.canvas.delete("all") # Limpa o canvas
                self.label_hitboxes.clear() # Limpa áreas clicáveis das labels
                transicoes_ativas = transicoes_ativas or set()
                agrupado = self._agrupar_transicoes() # Agrupa transições com formato JFLAP
                pares_processados = set() # Para evitar desenhar transições duplas duas vezes
                tipo = self.tipo_automato.get()
                current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1
                scaled_radius = STATE_RADIUS * self.zoom_level
                scaled_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)))
                bold_scaled_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)), "bold")
                
                # --- DESENHAR TRANSIÇÕES ---
                for origem_nome, destino_info in agrupado.items():
                    if origem_nome not in self.automato.estados or origem_nome not in self.positions: continue
                    origem = self.automato.estados[origem_nome]
                    x1, y1 = self._logical_to_view(*self.positions[origem_nome])
                    for destino_nome, simbolos in destino_info.items():
                        if destino_nome not in self.automato.estados or destino_nome not in self.positions: continue
                        destino = self.automato.estados[destino_nome]
                        x2, y2 = self._logical_to_view(*self.positions[destino_nome])
                        par = tuple(sorted((origem_nome, destino_nome)))
                        cor_linha = self.canvas_transicao_ativa[current_theme] if (origem_nome, destino_nome) in transicoes_ativas else self.canvas_fg_color[current_theme]
                        largura = 2.5 if (origem_nome, destino_nome) in transicoes_ativas else 1.5
                        label_exibicao = "\n".join(sorted(list(simbolos))) 
                        label_tag = f"label_{origem_nome}_{destino_nome}"
                        transicao_font = bold_scaled_font
                        transicao_color = self.canvas_fg_color[current_theme] # MUDANÇA
                        if origem_nome == destino_nome: # Loop
                            text_id = self.canvas.create_text(
                                x1, y1 - (75 * self.zoom_level), # Posição Y com zoom
                                text=label_exibicao, fill=transicao_color, 
                                font=transicao_font, anchor=tk.CENTER,
                                tags=("transition_label_text", label_tag))
                            p1_x, p1_y = x1 - (10*self.zoom_level), y1 - scaled_radius
                            c1_x, c1_y = x1 - (40*self.zoom_level), y1 - (scaled_radius + 35*self.zoom_level)
                            c2_x, c2_y = x1 + (40*self.zoom_level), y1 - (scaled_radius + 35*self.zoom_level)
                            p2_x, p2_y = x1 + (10*self.zoom_level), y1 - scaled_radius
                            self.canvas.create_line(p1_x, p1_y, c1_x, c1_y, c2_x, c2_y, p2_x, p2_y,
                                                    smooth=True, arrow=tk.LAST,
                                                    fill=cor_linha, width=largura, tags="linha_transicao")
                            bbox = self.canvas.bbox(text_id)
                            if bbox: self.label_hitboxes[label_tag] = bbox
                        elif agrupado.get(destino_nome, {}).get(origem_nome): # Transição dupla
                            if par in pares_processados: continue
                            cor_linha_volta = self.canvas_transicao_ativa[current_theme] if (destino_nome, origem_nome) in transicoes_ativas else self.canvas_fg_color[current_theme]
                            largura_volta = 2.5 if (destino_nome, origem_nome) in transicoes_ativas else 1.5
                            label_tag_volta = f"label_{destino_nome}_{origem_nome}"
                            label_volta_interna = ",".join(sorted(list(agrupado[destino_nome][origem_nome]))) 
                            label_ida_interna = ",".join(sorted(list(simbolos))) 
                            self._desenhar_linha_curva(origem, destino, label_ida_interna, 30, cor_linha, largura, label_tag)
                            self._desenhar_linha_curva(destino, origem, label_volta_interna, 30, cor_linha_volta, largura_volta, label_tag_volta)
                            pares_processados.add(par)
                        else: # Transição reta simples
                            dx, dy = x2 - x1, y2 - y1
                            dist = math.hypot(dx, dy) or 1
                            ux, uy = dx/dist, dy/dist
                            start_x, start_y = x1 + ux * scaled_radius, y1 + uy * scaled_radius
                            end_x, end_y = x2 - ux * scaled_radius, y2 - uy * scaled_radius
                            self.canvas.create_line(start_x, start_y, end_x, end_y,
                                                    arrow=tk.LAST,
                                                    fill=cor_linha, width=largura, tags="linha_transicao")
                            text_x = (start_x+end_x)/2 - uy*(15*self.zoom_level)
                            text_y = (start_y+end_y)/2 + ux*(15*self.zoom_level)
                            text_id = self.canvas.create_text(
                                text_x, text_y, text=label_exibicao,
                                fill=transicao_color, font=transicao_font,
                                anchor=tk.CENTER, tags=("transition_label_text", label_tag))
                            bbox = self.canvas.bbox(text_id)
                            if bbox: self.label_hitboxes[label_tag] = bbox

                # --- DESENHAR ESTADOS ---
                for nome, estado in self.automato.estados.items():
                    if nome not in self.positions: continue
                    x, y = self._logical_to_view(*self.positions[nome])
                    cor_borda_padrao = self.canvas_fg_color[current_theme]
                    if estados_ativos and nome in estados_ativos:
                        cor_borda = self.canvas_estado_ativo[current_theme] # Vermelho (simulação)
                    elif self.origem_transicao and nome == self.origem_transicao.nome:
                        cor_borda = self.cor_selecao_grupo[current_theme] # Azul (origem da transição)
                    elif nome in self.selection_group:
                        cor_borda = self.cor_selecao_grupo[current_theme] # Azul (selecionado)
                    else:
                        cor_borda = cor_borda_padrao
                    self.canvas.create_oval(x - scaled_radius, y - scaled_radius, x + scaled_radius, y + scaled_radius,
                                            fill=self.canvas_estado_fill[current_theme], # MUDANÇA
                                            outline=cor_borda, 
                                            width=3 if (cor_borda != cor_borda_padrao) else 2, # MUDANÇA
                                            tags=("estado_circulo", f"estado_{nome}"))
                    texto_estado = nome
                    if tipo == "Moore" and estado.output:
                        texto_estado = f"{nome}\n({estado.output})"
                    self.canvas.create_text(x, y, text=texto_estado, font=scaled_font,
                                            fill=self.canvas_estado_text[current_theme], # MUDANÇA
                                            justify=tk.CENTER,
                                            tags=("estado_texto", f"estado_{nome}_texto"))
                    if estado.is_final:
                        final_inner_radius = max(1, scaled_radius - (5 * self.zoom_level))
                        self.canvas.create_oval(x - final_inner_radius, y - final_inner_radius,
                                                x + final_inner_radius, y + final_inner_radius,
                                                outline=cor_borda, width=1,
                                                tags=("estado_final_circulo", f"estado_{nome}"))
                    if estado.is_inicial:
                        self.canvas.create_line(x - scaled_radius - (20 * self.zoom_level), y, x - scaled_radius, y,
                                                arrow=tk.LAST,
                                                width=2, fill=self.canvas_fg_color[current_theme], # MUDANÇA
                                                tags=("estado_inicial_seta", f"estado_{nome}"))
                # --- OUTROS ELEMENTOS ---
                if extra_info_str is not None:
                    scaled_info_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)))
                    tag = "Pilha: " if tipo == "AP" else ("Fita: " if tipo == "Turing" else "")
                    if tag:
                        bg_rect = self.canvas.create_rectangle(10, 10, 10 + len(tag + extra_info_str) * 8 + 10, 40,
                                                                fill=self.app_bg_color[current_theme], outline="", tags="extra_info_bg") # MUDANÇA
                        info_text = self.canvas.create_text(15, 25, text=f"{tag}{extra_info_str}", font=scaled_info_font,
                                                            fill=self.canvas_fg_color[current_theme], anchor="w", tags="extra_info_text") # MUDANÇA
                        text_bbox = self.canvas.bbox(info_text)
                        if text_bbox:
                            self.canvas.coords(bg_rect, 10, 10, text_bbox[2] + 5, 40)
            except Exception as e:
                print(f"Erro crítico ao desenhar automato: {e}")

    def _desenhar_linha_curva(self, origem, destino, label_original_virgula, fator, cor_linha, largura, label_tag):
            """Desenha uma linha curva entre dois estados com a label empilhada, preta e negrito."""
            if origem.nome not in self.positions or destino.nome not in self.positions: return
            current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1
            x1, y1 = self._logical_to_view(*self.positions[origem.nome])
            x2, y2 = self._logical_to_view(*self.positions[destino.nome])
            scaled_radius = STATE_RADIUS * self.zoom_level
            bold_scaled_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)), "bold")
            scaled_fator = fator * self.zoom_level
            scaled_text_offset = 15 * self.zoom_level
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1
            nx, ny = -dy/dist, dx/dist
            ux, uy = dx/dist, dy/dist
            start_x, start_y = x1 + ux * scaled_radius, y1 + uy * scaled_radius
            end_x, end_y = x2 - ux * scaled_radius, y2 - uy * scaled_radius
            mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            ctrl_x, ctrl_y = mid_x + nx * scaled_fator, mid_y + ny * scaled_fator
            self.canvas.create_line(start_x, start_y, ctrl_x, ctrl_y, end_x, end_y,
                                    smooth=True, arrow=tk.LAST,
                                    fill=cor_linha, width=largura, tags="linha_transicao")
            text_x = ctrl_x + nx * scaled_text_offset
            text_y = ctrl_y + ny * scaled_text_offset
            transicao_font = bold_scaled_font
            transicao_color = self.canvas_fg_color[current_theme] # MUDANÇA
            simbolos_lista = label_original_virgula.split(',') 
            label_empilhada = "\n".join(sorted(simbolos_lista)) 
            text_id = self.canvas.create_text(
                text_x, text_y, text=label_empilhada,
                fill=transicao_color, font=transicao_font,
                anchor=tk.CENTER, tags=("transition_label_text", label_tag))
            bbox = self.canvas.bbox(text_id)
            if bbox: self.label_hitboxes[label_tag] = bbox


    def _agrupar_transicoes(self):
        """Agrupa múltiplas transições entre os mesmos dois estados sob uma única label,
           formatada similarmente ao JFLAP."""
        agrupado = defaultdict(lambda: defaultdict(set))
        if not hasattr(self.automato, 'transicoes'): return agrupado
        trans_dict = self.automato.transicoes
        tipo = self.tipo_automato.get()
        epsilon_char = "ε" 
        blank_char = "☐" 

        if tipo == "AP":
            for (origem, s_in, s_pop), destinos_set in trans_dict.items():
                if destinos_set is None: continue
                for destino, s_push in destinos_set:
                    in_char = epsilon_char if s_in == EPSILON else s_in
                    pop_char = epsilon_char if s_pop == EPSILON else s_pop
                    push_char = epsilon_char if s_push == EPSILON else s_push
                    label = f"{in_char},{pop_char};{push_char}"
                    agrupado[origem][destino].add(label)
        elif tipo == "Mealy":
                for (origem, simbolo), (destino, output) in trans_dict.items():
                    in_char = epsilon_char if simbolo == EPSILON else simbolo
                    out_char = epsilon_char if output == EPSILON else output
                    label = f"{in_char} ; {out_char}" # MUDANÇA: ;
                    agrupado[origem][destino].add(label)
        elif tipo == "Turing":
                simbolo_branco_automato = getattr(self.automato, 'simbolo_branco', '☐')
                for (origem, lido), (destino, escrito, direcao) in trans_dict.items():
                    read_char = blank_char if lido == simbolo_branco_automato else lido
                    write_char = blank_char if escrito == simbolo_branco_automato else escrito
                    label = f"{read_char} ; {write_char} , {direcao}" # MUDANÇA: ;
                    agrupado[origem][destino].add(label)
        else: # AFD, AFN, Moore
            for (origem, simbolo), destinos in trans_dict.items():
                label_sym = epsilon_char if simbolo == EPSILON else simbolo
                if isinstance(destinos, set): # AFN
                    for destino in destinos:
                        agrupado[origem][destino].add(label_sym)
                else: # AFD, Moore
                    if destinos:
                        agrupado[origem][destinos].add(label_sym)
        return agrupado

    # --- FUNÇÕES DE SIMULAÇÃO ... (Nenhuma mudança nesta seção) ...
    def iniciar_simulacao(self):
        """Inicia a simulação passo a passo do autômato com a cadeia de entrada."""
        self.parar_simulacao(final_state=False) # Reseta simulação anterior
        cadeia = self.entrada_cadeia.get()
        tipo = self.tipo_automato.get()
        current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1 # NOVO
        self.lbl_cadeia_consumida.configure(text="")
        self.lbl_cadeia_restante.configure(text=cadeia if tipo not in ["Turing"] else "", text_color=self.default_fg_color[current_theme])
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
        self.lbl_status_simulacao.configure(text="Simulando...", text_color=self.default_fg_color[current_theme])
        self.executar_proximo_passo() 
    def parar_simulacao(self, final_state=False):
        """Para a simulação atual e reseta a UI para o estado inicial."""
        self.simulador = None 
        current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1 
        self.btn_simular.configure(text="▶ Iniciar", command=self.iniciar_simulacao)
        self.btn_proximo_passo.configure(state="disabled")
        if not final_state:
            self.lbl_status_simulacao.configure(text="Status: Aguardando", text_color=self.default_fg_color[current_theme])
            self.lbl_cadeia_consumida.configure(text="", text_color=self.cor_consumida[current_theme]) # Reseta cor
            self.lbl_cadeia_restante.configure(text="", text_color=self.default_fg_color[current_theme])
            self.lbl_output_valor.configure(text="")
            self.lbl_tape_valor.configure(text="")
            self.desenhar_automato() 
    def executar_proximo_passo(self):
        """Executa o próximo passo da simulação e atualiza a UI."""
        if not self.simulador: return 
        current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1 
        passo_info = self.simulador.proximo_passo() 
        tipo = self.tipo_automato.get()
        if not passo_info:
            current_status_text = self.lbl_status_simulacao.cget("text")
            if current_status_text == "Simulando..." or current_status_text == "Status: Aguardando":
                aceitou = False
                try: 
                    last_step_vars = self.simulador.gerador.gi_frame.f_locals
                    last_active_states_raw = last_step_vars.get('estado_atual', last_step_vars.get('estados_atuais', set()))
                    if isinstance(last_active_states_raw, str): last_active_states = {last_active_states_raw}
                    elif isinstance(last_active_states_raw, set): last_active_states = last_active_states_raw
                    else: last_active_states = set()
                    if last_active_states and hasattr(self.simulador, 'automato') and self.simulador.automato.estados_finais:
                        aceitou = any(e in self.simulador.automato.estados_finais
                                    for e in last_active_states if e in self.simulador.automato.estados)
                except Exception as e:
                    print(f"Erro ao verificar estado final: {e}")
                if aceitou: 
                    self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita[current_theme])
                    if tipo != "Turing":
                        self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get(), text_color=self.cor_aceita[current_theme])
                        self.lbl_cadeia_restante.configure(text="")
                else: 
                    self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita[current_theme])
                    if tipo != "Turing":
                        self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get(), text_color=self.cor_rejeita[current_theme])
                        self.lbl_cadeia_restante.configure(text="")
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
            cor_consumo = self.cor_consumida[current_theme] # Padrão (verde)
            cor_restante = self.default_fg_color[current_theme] # Padrão (default)
            if status == "rejeita":
                cor_consumo = self.cor_rejeita[current_theme] # Vermelho se rejeitado
                cor_restante = self.cor_rejeita[current_theme] # Vermelho se rejeitado
            self.lbl_cadeia_consumida.configure(text=cadeia_consumida, text_color=cor_consumo) 
            self.lbl_cadeia_restante.configure(text=cadeia_restante, text_color=cor_restante) # <-- COR APLICADA
        elif tipo == "Turing":
                self.lbl_cadeia_consumida.configure(text="")
                self.lbl_cadeia_restante.configure(text="")
        if status == "executando":
            self.desenhar_automato(passo_info["estado_atual"], passo_info.get("transicao_ativa"), extra_info_canvas)
        elif status == "aceita":
            self.lbl_status_simulacao.configure(text="Palavra Aceita", text_color=self.cor_aceita[current_theme])
            if tipo != "Turing": 
                self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get(), text_color=self.cor_aceita[current_theme])
                self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True) 
        elif status == "rejeita":
            self.lbl_status_simulacao.configure(text="Palavra Não Aceita", text_color=self.cor_rejeita[current_theme])
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True)
        elif status == "finalizado": # Usado por Moore/Mealy
            self.lbl_status_simulacao.configure(text="Processamento Concluído", text_color=self.cor_finalizado[current_theme])
            if tipo != "Turing": 
                self.lbl_cadeia_consumida.configure(text=self.entrada_cadeia.get(), text_color=self.cor_consumida[current_theme]) 
                self.lbl_cadeia_restante.configure(text="")
            self.desenhar_automato(passo_info.get("estado_atual"), passo_info.get("transicao_ativa"), extra_info_canvas)
            self.parar_simulacao(final_state=True)
        elif status == "erro": # Erro durante a simulação
            messagebox.showerror("Erro", passo_info["mensagem"])
            self.parar_simulacao()


    # --- MÉTODOS DE EXPORTAÇÃO E IMPORTAÇÃO ---

    def importar_de_jff(self):
        """
        Abre um arquivo .jff e carrega o autômato no simulador.
        MODIFICADO: Reseta o histórico de undo/redo.
        """
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("JFLAP files", "*.jff"), ("All files", "*.*")],
                title="Abrir Arquivo JFF",
                parent=self.master
            )
            if not filepath: return 

            tree = ET.parse(filepath)
            root = tree.getroot()

            # 1. Obter o tipo de autômato
            jflap_type_node = root.find("type")
            if jflap_type_node is None: raise ValueError("Arquivo JFF inválido: tag <type> não encontrada.")
            jflap_type = jflap_type_node.text.lower()
            automaton_node = root.find("automaton")
            if automaton_node is None: raise ValueError("Arquivo JFF inválido: tag <automaton> não encontrada.")

            tipo_simulador = ""
            if jflap_type == "fa": tipo_simulador = "AFD" 
            elif jflap_type == "pda": tipo_simulador = "AP"
            elif jflap_type == "turing": tipo_simulador = "Turing"
            elif jflap_type == "mealy":
                if automaton_node.find("state/output") is not None: tipo_simulador = "Moore"
                else: tipo_simulador = "Mealy"
            else:
                raise ValueError(f"Tipo de autômato JFLAP '{jflap_type}' não suportado.")

            # 2. Limpar a tela e configurar o novo tipo (MODIFICADO)
            self.tipo_automato.set(tipo_simulador)
            # Reseta a tela E o histórico, sem salvar o estado anterior
            self.limpar_tela(save_current_state=False, reset_history=True) 

            # 3. Mapear IDs de estado ... (Lógica de importação normal) ...
            id_to_name = {}
            states_nodes = automaton_node.findall("state")
            state_data_map = {} 
            self.contador_estados = 0 
            for state in states_nodes:
                state_id = state.get("id"); state_name = state.get("name")
                if not state_name: state_name = f"q{self.contador_estados}"
                while state_name in self.automato.estados or state_name in (d['name'] for d in state_data_map.values()):
                        self.contador_estados += 1; state_name = f"q{self.contador_estados}"
                id_to_name[state_id] = state_name
                x_node = state.find("x"); y_node = state.find("y")
                x_pos = float(x_node.text) if x_node is not None and x_node.text else (50.0 + int(state_id) * 80)
                y_pos = float(y_node.text) if y_node is not None and y_node.text else 50.0
                state_data_map[state_id] = {
                    'name': state_name, 'x': x_pos, 'y': y_pos,
                    'is_initial': state.find("initial") is not None,
                    'is_final': state.find("final") is not None,
                    'output': state.find("output").text if state.find("output") is not None else ""
                }
            # 4. Adicionar Estados
            for state_id, data in state_data_map.items():
                self.positions[data['name']] = (data['x'], data['y'])
                output_val = data['output'] if tipo_simulador == "Moore" else ""
                if tipo_simulador == "Moore": self.automato.adicionar_estado(data['name'], data['x'], data['y'], output=output_val)
                else: self.automato.adicionar_estado(data['name'], data['x'], data['y'])
            # 5. Definir estados Iniciais e Finais
            for state_id, data in state_data_map.items():
                    if data['is_initial']: self.automato.definir_estado_inicial(data['name'])
                    if data['is_final']:
                        if hasattr(self.automato, 'adicionar_estado_final'): self.automato.adicionar_estado_final(data['name'])
                        else: self.automato.alternar_estado_final(data['name'])
            # 6. Adicionar Transições
            transition_nodes = automaton_node.findall("transition")
            if tipo_simulador == "AFD":
                transitions_check = {}; is_afn = False
                for trans in transition_nodes:
                    from_id = trans.find("from").text
                    read_node = trans.find("read")
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    chave = (from_id, simbolo)
                    if chave in transitions_check: is_afn = True; break
                    transitions_check[chave] = True
                    if simbolo == EPSILON: is_afn = True; break
                if is_afn:
                    print("Autômato 'fa' detectado como AFN. Recarregando como AFN.")
                    tipo_simulador = "AFN"; self.tipo_automato.set("AFN")
                    self.limpar_tela(save_current_state=False, reset_history=True) # <--- MODIFICADO
                    for state_id, data in state_data_map.items():
                        self.positions[data['name']] = (data['x'], data['y'])
                        self.automato.adicionar_estado(data['name'], data['x'], data['y'])
                    for state_id, data in state_data_map.items():
                            if data['is_initial']: self.automato.definir_estado_inicial(data['name'])
                            if data['is_final']:
                                if hasattr(self.automato, 'adicionar_estado_final'): self.automato.adicionar_estado_final(data['name'])
                                else: self.automato.alternar_estado_final(data['name'])
            # Processa as transições
            for trans in transition_nodes:
                from_name = id_to_name.get(trans.find("from").text)
                to_name = id_to_name.get(trans.find("to").text)
                if not from_name or not to_name: continue 
                if tipo_simulador in ["AFD", "AFN", "Moore"]:
                    read_node = trans.find("read")
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    self.automato.adicionar_transicao(from_name, simbolo, to_name)
                elif tipo_simulador == "AP":
                    read_node = trans.find("read"); pop_node = trans.find("pop"); push_node = trans.find("push")
                    s_in = EPSILON if read_node is None or read_node.text is None else read_node.text
                    s_pop = EPSILON if pop_node is None or pop_node.text is None else pop_node.text
                    s_push = EPSILON if push_node is None or push_node.text is None else push_node.text
                    self.automato.adicionar_transicao(from_name, s_in, s_pop, to_name, s_push)
                elif tipo_simulador == "Mealy":
                    read_node = trans.find("read"); transout_node = trans.find("transout")
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    output = EPSILON if transout_node is None or transout_node.text is None else transout_node.text
                    self.automato.adicionar_transicao(from_name, simbolo, to_name, output)
                elif tipo_simulador == "Turing":
                    read_node = trans.find("read"); write_node = trans.find("write"); move_node = trans.find("move")
                    simbolo_branco_auto = self.automato.simbolo_branco
                    lido = simbolo_branco_auto if read_node is None or read_node.text is None else read_node.text
                    escrito = simbolo_branco_auto if write_node is None or write_node.text is None else write_node.text
                    direcao = move_node.text if move_node is not None else "R"
                    self.automato.adicionar_transicao(from_name, lido, to_name, escrito, direcao)

            # 7. Redesenhar e Salvar Estado (MODIFICADO)
            self.zoom_slider.set(1.0) 
            self.desenhar_automato()
            
            # --- NOVO: Salva o estado recém-carregado no histórico ---
            self._save_history_state()
            self._update_history_buttons() # Atualiza botões (redo será desabilitado)
            
            messagebox.showinfo("Importar JFF", f"Autômato carregado com sucesso de:\n{filepath}", parent=self.master)

        except ET.ParseError:
            messagebox.showerror("Erro ao Importar JFF", "O arquivo selecionado não é um XML válido.", parent=self.master)
            self.limpar_tela(save_current_state=False, reset_history=True) # <--- MODIFICADO
        except Exception as e:
            messagebox.showerror("Erro ao Importar JFF", f"Ocorreu um erro ao processar o arquivo:\n{e}", parent=self.master)
            self.limpar_tela(save_current_state=False, reset_history=True) # <--- MODIFICADO


    def exportar_para_jpg(self):
        """Salva a área atual do canvas como uma imagem JPG."""
        if not self.automato or not self.automato.estados:
                messagebox.showwarning("Exportar JPG", "Não há autômato para exportar.", parent=self.master)
                return
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")],
                title="Salvar Autômato como JPG",
                parent=self.master
            )
            if not filepath: return 
            x = self.canvas.winfo_rootx(); y = self.canvas.winfo_rooty()
            x1 = x + self.canvas.winfo_width(); y1 = y + self.canvas.winfo_height()
            margin = 2 
            img = ImageGrab.grab(bbox=(x + margin, y + margin, x1 - margin, y1 - margin))
            img.save(filepath, "JPEG") 
            messagebox.showinfo("Exportar JPG", f"Autômato salvo como JPG em:\n{filepath}", parent=self.master)
        except Exception as e: 
            messagebox.showerror("Erro ao Exportar JPG", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JPG: {e}")


    def exportar_para_jff(self):
        """Converte o autômato atual para o formato JFLAP (.jff) e salva em arquivo."""
        # ... (Nenhuma mudança nesta função) ...
        if not self.automato or not self.automato.estados:
            messagebox.showwarning("Exportar JFF", "Não há autômato para exportar.", parent=self.master)
            return
        automato_tipo = self.tipo_automato.get().lower()
        jflap_type = "fa" 
        if automato_tipo == "ap": jflap_type = "pda"
        elif automato_tipo == "turing": jflap_type = "turing"
        elif automato_tipo in ["moore", "mealy"]: jflap_type = "mealy" 
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jff",
                filetypes=[("JFLAP files", "*.jff"), ("All files", "*.*")],
                title="Salvar Autômato como JFF",
                parent=self.master
            )
            if not filepath: return 
            root = ET.Element("structure")
            ET.SubElement(root, "type").text = jflap_type
            automaton_element = ET.SubElement(root, "automaton")
            state_to_id = {name: str(i) for i, name in enumerate(self.automato.estados.keys())}
            for name, estado in self.automato.estados.items():
                state_id = state_to_id[name]
                state_element = ET.SubElement(automaton_element, "state", id=state_id, name=name)
                x_pos, y_pos = self.positions.get(name, (50.0 + int(state_id)*80, 50.0))
                ET.SubElement(state_element, "x").text = str(float(x_pos))
                ET.SubElement(state_element, "y").text = str(float(y_pos))
                if estado.is_inicial: ET.SubElement(state_element, "initial")
                if estado.is_final: ET.SubElement(state_element, "final")
                if automato_tipo == "moore" and hasattr(estado, 'output') and estado.output:
                        ET.SubElement(state_element, "output").text = estado.output
            if jflap_type == "fa": # AFD/AFN
                for (origem, simbolo), destinos in self.automato.transicoes.items():
                    origem_id = state_to_id.get(origem)
                    if origem_id is None: continue
                    destinos_set = destinos if isinstance(destinos, set) else {destinos}
                    for destino in destinos_set:
                        destino_id = state_to_id.get(destino)
                        if destino_id is None: continue
                        trans_element = ET.SubElement(automaton_element, "transition")
                        ET.SubElement(trans_element, "from").text = origem_id
                        ET.SubElement(trans_element, "to").text = destino_id
                        read_element = ET.SubElement(trans_element, "read")
                        if simbolo != EPSILON: read_element.text = simbolo 
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
                    simbolo_branco_automato = getattr(self.automato, 'simbolo_branco', 'B') 
                    for (origem, lido), (destino, escrito, direcao) in self.automato.transicoes.items():
                        origem_id = state_to_id.get(origem)
                        destino_id = state_to_id.get(destino)
                        if origem_id is None or destino_id is None: continue
                        trans_element = ET.SubElement(automaton_element, "transition")
                        ET.SubElement(trans_element, "from").text = origem_id
                        ET.SubElement(trans_element, "to").text = destino_id
                        read_element = ET.SubElement(trans_element, "read")
                        if lido != simbolo_branco_automato: read_element.text = lido
                        write_element = ET.SubElement(trans_element, "write")
                        if escrito != simbolo_branco_automato: write_element.text = escrito
                        move_element = ET.SubElement(trans_element, "move")
                        move_element.text = direcao
            elif jflap_type == "mealy": # Mealy (e Moore)
                    for (origem, simbolo), (destino, output) in self.automato.transicoes.items():
                        origem_id = state_to_id.get(origem)
                        destino_id = state_to_id.get(destino)
                        if origem_id is None or destino_id is None: continue
                        trans_element = ET.SubElement(automaton_element, "transition")
                        ET.SubElement(trans_element, "from").text = origem_id
                        ET.SubElement(trans_element, "to").text = destino_id
                        read_element = ET.SubElement(trans_element, "read")
                        if simbolo != EPSILON: read_element.text = simbolo
                        output_element = ET.SubElement(trans_element, "transout") 
                        if output != EPSILON: output_element.text = output
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml_str = dom.toprettyxml(indent="  ")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                f.write(pretty_xml_str.split('\n', 1)[1])
            messagebox.showinfo("Exportar JFF", f"Autômato salvo como JFF em:\n{filepath}", parent=self.master)
        except Exception as e: 
            messagebox.showerror("Erro ao Exportar JFF", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JFF: {e}")


# --- CLASSES DE DIÁLOGO (COM A NOVA CLASSE ADICIONADA) ---

# --- NOVO: Diálogo para transições simples (AFD, AFN, Moore) ---
class TransicaoSimplesDialog(ctk.CTkToplevel):
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Editar Transição"); self.resultado = None; self.geometry("300x200")
        if style_dict is None: style_dict = {}
        
        self.transient(parent) # Mantém o diálogo na frente
        self.grab_set() # Modal
        
        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))
        ctk.CTkLabel(self, text="Símbolo(s) (e=vazio, ',' para separar):").pack(padx=20, pady=(10,0))
        
        # Este é o CTkEntry que podemos acessar com segurança
        self.e_simbolos = ctk.CTkEntry(self, **style_dict)
        self.e_simbolos.pack(padx=20, pady=5, fill="x")
        
        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)
        self.e_simbolos.focus() # Foca no campo de entrada
        
    def ok(self):
        # Apenas retorna o texto bruto, a lógica de split/epsilon é feita na tela principal
        self.resultado = self.e_simbolos.get()
        self.destroy()

# --- Diálogo para selecionar uma transição de um grupo ---
class TransicaoSelectorDialog(ctk.CTkToplevel):
    """
    Um diálogo modal para permitir ao usuário selecionar qual transição editar
    quando múltiplas transições existem na mesma seta.
    """
    def __init__(self, parent, origem, destino, labels, style_dict=None):
        super().__init__(parent)
        self.title("Selecionar Transição")
        self.resultado_index = None
        self.labels = labels
        self.selected_var = tk.IntVar(value=-1)
        if style_dict is None: style_dict = {}

        self.geometry(f"350x{150 + len(labels) * 35}") # Ajusta a altura
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=f"Editar Transição de {origem} para {destino}", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=20, pady=(15,5))
        ctk.CTkLabel(self, text="Múltiplas transições encontradas.\nSelecione uma para editar:").pack(padx=20, pady=5)

        radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        radio_frame.pack(padx=20, pady=10, fill="x", expand=True)

        for i, label in enumerate(labels):
            ctk.CTkRadioButton(
                radio_frame, 
                text=label, 
                variable=self.selected_var, 
                value=i,
                font=ctk.CTkFont(family="Courier New", size=12)
            ).pack(anchor="w", pady=3)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(10,15))
        
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.cancel, **style_dict).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="OK", command=self.ok, **style_dict).pack(side="left", padx=5)

    def ok(self):
        idx = self.selected_var.get()
        if idx == -1:
            messagebox.showwarning("Seleção Inválida", "Por favor, selecione uma transição para editar.", parent=self)
            return
        self.resultado_index = idx
        self.destroy()

    def cancel(self):
        self.resultado_index = None
        self.destroy()


# Diálogos modais para inserir informações de transição
class TransicaoPilhaDialog(ctk.CTkToplevel):
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição AP"); self.resultado = None; self.geometry("300x350")
        if style_dict is None: style_dict = {}
        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))
        ctk.CTkLabel(self, text="Entrada (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_entrada = ctk.CTkEntry(self, **style_dict); self.e_entrada.pack(padx=20, pady=5); self.e_entrada.insert(0, 'e') 
        ctk.CTkLabel(self, text="Desempilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_pop = ctk.CTkEntry(self, **style_dict); self.e_pop.pack(padx=20, pady=5); self.e_pop.insert(0, 'e')
        ctk.CTkLabel(self, text="Empilha (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_push = ctk.CTkEntry(self, **style_dict); self.e_push.pack(padx=20, pady=5); self.e_push.insert(0, 'e')
        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)
        self.grab_set(); self.e_entrada.focus() 
    
    def ok(self):
        # --- LÓGICA CORRIGIDA ---
        ent = self.e_entrada.get().strip()
        pop = self.e_pop.get().strip()
        push = self.e_push.get().strip()
        
        self.resultado = {
            'entrada': EPSILON if ent == 'e' or ent == '' else ent,
            'pop': EPSILON if pop == 'e' or pop == '' else pop,
            'push': EPSILON if push == 'e' or push == '' else push
        }; self.destroy() 
        
class TransicaoMealyDialog(ctk.CTkToplevel):
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição Mealy"); self.resultado = None; self.geometry("300x280")
        if style_dict is None: style_dict = {}
        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))
        ctk.CTkLabel(self, text="Símbolo de Entrada (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_simbolo = ctk.CTkEntry(self, **style_dict); self.e_simbolo.pack(padx=20, pady=5); self.e_simbolo.insert(0, 'e')
        ctk.CTkLabel(self, text="Símbolo de Saída (e=vazio):").pack(padx=20, pady=(10,0))
        self.e_output = ctk.CTkEntry(self, **style_dict); self.e_output.pack(padx=20, pady=5); self.e_output.insert(0, 'e')
        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)
        self.grab_set(); self.e_simbolo.focus()
        
    def ok(self):
        # --- LÓGICA CORRIGIDA ---
        simbolo_input = self.e_simbolo.get().strip()
        output_input = self.e_output.get().strip()
        
        simbolo_final = EPSILON if simbolo_input == 'e' or simbolo_input == '' else simbolo_input
        output_final = EPSILON if output_input == 'e' or output_input == '' else output_input
        
        self.resultado = {
            'simbolo': simbolo_final, 
            'output': output_final
        }; self.destroy()
        
class TransicaoTuringDialog(ctk.CTkToplevel):
    def __init__(self, parent, origem, destino, style_dict=None):
        super().__init__(parent)
        self.title(f"Transição Turing"); self.resultado = None; self.geometry("300x350")
        if style_dict is None: style_dict = {}
        ctk.CTkLabel(self, text=f"{origem}  ->  {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10,5))
        ctk.CTkLabel(self, text="Símbolo Lido:").pack(padx=20, pady=(10,0))
        self.e_lido = ctk.CTkEntry(self, **style_dict); self.e_lido.pack(padx=20, pady=5); self.e_lido.insert(0, '☐') 
        ctk.CTkLabel(self, text="Símbolo Escrito:").pack(padx=20, pady=(10,0))
        self.e_escrito = ctk.CTkEntry(self, **style_dict); self.e_escrito.pack(padx=20, pady=5); self.e_escrito.insert(0, '☐')
        ctk.CTkLabel(self, text="Direção (L/R):").pack(padx=20, pady=(10,0))
        self.e_dir = ctk.CTkEntry(self, width=50, **style_dict) ; self.e_dir.pack(padx=20, pady=5); self.e_dir.insert(0, 'R') 
        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)
        self.grab_set(); self.e_lido.focus()
        
    def ok(self):
        # --- LÓGICA CORRIGIDA ---
        lido = self.e_lido.get().strip() or '☐'
        escrito = self.e_escrito.get().strip() or '☐'
        direcao = (self.e_dir.get().strip() or 'R').upper() 
        
        if direcao not in ['L', 'R']:
            messagebox.showerror("Erro", "Direção deve ser 'L' ou 'R'.", parent=self); return
        # Permite string vazia para o símbolo branco (JFLAP)
        if len(lido) > 1 or len(escrito) > 1:
                messagebox.showerror("Erro", "Símbolos da fita devem ter apenas 1 caractere.", parent=self); return
        
        # Converte string vazia para o símbolo branco padrão, se necessário
        lido_final = lido if lido else '☐'
        escrito_final = escrito if escrito else '☐'

        self.resultado = {
            'lido': lido_final, 
            'escrito': escrito_final, 
            'dir': direcao
        }; self.destroy()