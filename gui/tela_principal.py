import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog # Adicionado filedialog
import math
import os # Adicionado os
import xml.etree.ElementTree as ET # Adicionado ET para JFF
from xml.dom import minidom # Adicionado minidom para JFF
from PIL import ImageGrab, Image # Adicionado ImageGrab e Image para JPG

# --- Imports de módulos locais (simulados para o exemplo) ---
# Certifique-se de que esses arquivos existem no seu projeto.
# Se os nomes dos arquivos/classes estiverem errados, ajuste-os.
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
        def deletar_transicoes_entre(self, o, d): pass
        def adicionar_transicao(self, *args, **kwargs): pass
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

        # --- Cores e Estilos (Alinhados com tela_menu.py) ---
        self.default_fg_color = (ctk.ThemeManager.theme["CTkLabel"]["text_color"][0], ctk.ThemeManager.theme["CTkLabel"]["text_color"][1])
        
        # Cores base
        self.app_bg_color = ("gray85", "gray20")
        self.cor_verde_fg = ("#4CAF50", "#388E3C")
        self.cor_verde_hover = ("#388E3C", "#2E7D32")
        self.cor_azul_fg = ("#2196F3", "#1976D2")
        self.cor_azul_hover = ("#1976D2", "#1565C0")
        self.cor_vermelha_fg = ("#d32f2f", "#d32f2f") # Tupla para consistência
        self.cor_vermelha_hover = ("#b71c1c", "#b71c1c") # Tupla para consistência
        self.cor_cinza_fg = ("#565b5e", "#565b5e")
        self.cor_cinza_hover = ("#4a4f52", "#4a4f52")

        # Cores de status da simulação
        self.cor_consumida = self.cor_verde_fg
        self.cor_aceita = self.cor_verde_fg
        self.cor_rejeita = self.cor_vermelha_fg
        self.cor_finalizado = self.cor_azul_fg 
        
        # Cores do Canvas
        self.canvas_bg = ("#FFFFFF", "#2B2B2B") # Canvas branco (light) / cinza escuro (dark)
        self.canvas_fg_color = ("black", "white") # Cor da linha da transição
        self.canvas_estado_fill = ("white", "#343638")
        self.canvas_estado_text = ("black", "white")
        self.canvas_transicao_text = self.cor_azul_fg # Texto da transição azul
        self.canvas_transicao_ativa = self.cor_verde_fg
        self.canvas_estado_ativo = self.cor_vermelha_fg # Estado ativo na simulação
        self.cor_selecao_grupo = self.cor_azul_fg # Estado selecionado no modo Mover

        # Cores semânticas dos botões
        self.cor_destrutiva_fg = self.cor_vermelha_fg
        self.cor_destrutiva_hover = self.cor_vermelha_hover
        self.cor_navegacao_fg = self.cor_cinza_fg 
        self.cor_navegacao_hover = self.cor_cinza_hover
        self.cor_ferramenta_fg = self.cor_azul_fg # Ferramentas agora são azuis
        self.cor_ferramenta_hover = self.cor_azul_hover
        self.cor_simulacao_fg = self.cor_verde_fg # Botões de simulação são verdes
        self.cor_simulacao_hover = self.cor_verde_hover

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

        # --- NOVAS VARIÁVEIS PARA SELEÇÃO MÚLTIPLA ---
        self.selection_box_start = None
        self.selection_box_id = None   
        self.selection_group = set()    
        self.drag_start_pos = None     

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

        self.btn_theme_toggle = ctk.CTkButton(top_bar, text="",
                                            command=self.toggle_theme, width=120,
                                            **self.style_top_widget)
        self.btn_theme_toggle.pack(side="left", padx=10)
        
        # --- NOVO BOTÃO DE ABRIR ---
        self.btn_open_jff = ctk.CTkButton(top_bar, text="📂 Abrir JFF",
                                            command=self.importar_de_jff, width=120,
                                            fg_color=self.cor_ferramenta_fg, # Azul
                                            hover_color=self.cor_ferramenta_hover,
                                            **self.style_top_widget)
        self.btn_open_jff.pack(side="left", padx=(20, 5))
        # --- FIM DO NOVO BOTÃO ---

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

        # --- 2. Barra de Ferramentas ---

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


        # --- 3. Canvas e Slider de Zoom (MODIFICADO) ---
        
        # Cria um frame principal para o canvas e o slider
        canvas_frame = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
        canvas_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=0) # Coluna do Slider
        canvas_frame.grid_columnconfigure(1, weight=1) # Coluna do Canvas

        # Adiciona o Slider de Zoom
        self.zoom_slider = ctk.CTkSlider(
            canvas_frame,
            from_=0.2,
            to=3.0,
            number_of_steps=28,
            orientation="vertical",
            command=self.on_zoom_change,
            button_color=self.cor_ferramenta_fg,      # Cor do botão (Azul)
            button_hover_color=self.cor_ferramenta_hover
        )
        self.zoom_slider.grid(row=0, column=0, sticky="ns", padx=(0, 5))
        self.zoom_slider.set(1.5) # Modificado: Define o zoom inicial como 150%

        # Adiciona o Canvas (agora dentro do 'canvas_frame')
        self.canvas = tk.Canvas(canvas_frame, bg=self.canvas_bg[0], bd=0, highlightthickness=0) # MUDANÇA: Cor do canvas
        self.canvas.grid(row=0, column=1, sticky="nsew") 


        # --- 4. Frame Fita/Saída ---
        self.frame_extra_info = ctk.CTkFrame(master, fg_color=self.app_bg_color) # MUDANÇA: Fundo
        self.frame_extra_info.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.frame_extra_info.grid_columnconfigure(1, weight=1)

        self.lbl_output_tag = ctk.CTkLabel(self.frame_extra_info, text="Saída:", font=ctk.CTkFont(weight="bold"))
        self.lbl_output_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.cor_finalizado)

        self.lbl_tape_tag = ctk.CTkLabel(self.frame_extra_info, text="Fita:", font=ctk.CTkFont(weight="bold"))
        self.lbl_tape_valor = ctk.CTkLabel(self.frame_extra_info, text="", font=ctk.CTkFont(family="Courier New", size=16, weight="bold"))

        # --- 5. Barra Inferior (Simulação) ---
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

        self.mudar_tipo_automato()
        self.set_active_mode("MOVER")
        self.btn_proximo_passo.configure(state="disabled")
        self._atualizar_widgets_extra_info()

        self.sync_theme()


    # --- NOVAS FUNÇÕES DE ZOOM ---

    def on_zoom_change(self, value):
        """Chamado pelo slider de zoom. Atualiza o nível de zoom e redesenha."""
        self.zoom_level = float(value)
        self.desenhar_automato()

    def _logical_to_view(self, x, y):
        """Converte coordenadas lógicas (do modelo) para visuais (do canvas)."""
        view_x = x * self.zoom_level
        view_y = y * self.zoom_level
        return view_x, view_y

    def _view_to_logical(self, x, y):
        """Converte coordenadas visuais (do canvas/mouse) para lógicas (do modelo)."""
        if self.zoom_level == 0: # Evita divisão por zero
            return x, y
        logical_x = x / self.zoom_level
        logical_y = y / self.zoom_level
        return logical_x, logical_y

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
        # Nota: Não é ideal chamar desenhar_automato() aqui por performance.
        # O clique no canvas subseqüente irá limpar visualmente a seleção.

    # --- FUNÇÕES DE TEMA (MODIFICADAS) ---

    def sync_theme(self):
        """
        CORREÇÃO: Aplica as cores do tema atual aos widgets personalizados (como o canvas).
        Não troca o tema, apenas sincroniza as cores.
        """
        current_mode = ctk.get_appearance_mode()
        current_theme_index = 0 if current_mode == "Light" else 1

        self.update_theme_button_text() # Atualiza o texto do botão de tema

        # Atualiza cores dependentes do tema e redesenha
        self.default_fg_color = (ctk.ThemeManager.theme["CTkLabel"]["text_color"][0], ctk.ThemeManager.theme["CTkLabel"]["text_color"][1])
        self.update_button_styles()
        
        # --- MUDANÇA: Atualiza a cor de fundo do canvas manualmente ---
        self.canvas.configure(bg=self.canvas_bg[current_theme_index])
        
        self.desenhar_automato()

    def toggle_theme(self):
        """
        CORREÇÃO: Alterna entre o tema claro e escuro e chama sync_theme para aplicar.
        """
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

        # Apenas chama a função de sincronização após trocar o tema
        self.sync_theme()

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
        self.selection_group.clear() # Limpa seleção
        self.parar_simulacao(final_state=False) # Para e reseta a simulação
        self.set_active_mode("MOVER") # Volta para o modo padrão
        self.desenhar_automato() # Limpa e redesenha o canvas
        self._atualizar_widgets_extra_info() # Atualiza widgets extras


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
                # 1. Se o estado clicado NÃO está na seleção atual:
                #    Limpe a seleção antiga e selecione apenas este.
                if estado_clicado.nome not in self.selection_group:
                    self.selection_group.clear()
                    self.selection_group.add(estado_clicado.nome)
                
                # 2. Se o estado JÁ está na seleção, não faça nada (permite arrastar o grupo)
                
                self.estado_movendo = estado_clicado # Indica que o drag começou *sobre* um estado
                self.drag_start_pos = (event.x, event.y) # Armazena início do drag

            elif not estado_clicado and not transicao_clicada: # Clicou no vazio
                self.estado_movendo = None
                self.selection_group.clear() # Limpa seleção anterior
                self.selection_box_start = (event.x, event.y) # Inicia o box-select
                self.drag_start_pos = (event.x, event.y) # Armazena início do drag
                
                # Cria o retângulo de seleção
                if self.selection_box_id:
                    self.canvas.delete(self.selection_box_id)
                self.selection_box_id = self.canvas.create_rectangle(
                    event.x, event.y, event.x, event.y, 
                    fill="#007acc", stipple="gray25", outline="#007acc" # Azul semi-transparente
                )
            
            self.desenhar_automato() # Redesenha para mostrar nova seleção
            return # Não processe outros modos

        # --- OUTROS MODOS ---
        # Se não estava no modo MOVER, limpe a seleção antes de fazer outra coisa
        self.selection_group.clear() 

        if mode == "ESTADO" and not estado_clicado and not transicao_clicada:
            nome_estado = f"q{self.contador_estados}"
            while nome_estado in self.automato.estados:
                self.contador_estados += 1; nome_estado = f"q{self.contador_estados}"

            if self.tipo_automato.get() == "Moore":
                dialog = ctk.CTkInputDialog(text="Símbolo de Saída do Estado (vazio=default):", title="Criar Estado Moore")
                output = dialog.get_input()
                if output is None: return
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
            elif mode == "INICIAL": self.automato.definir_estado_inicial(estado_clicado.nome)
            elif mode == "FINAL": self.automato.alternar_estado_final(estado_clicado.nome)
            elif mode == "DELETAR":
                nome_a_deletar = estado_clicado.nome
                self.automato.deletar_estado(nome_a_deletar)
                self.positions.pop(nome_a_deletar, None)
                
        elif transicao_clicada and mode == "DELETAR":
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

    def arrastar_canvas(self, event):
        """Move o estado selecionado ou o grupo de seleção."""
        if self.current_mode != "MOVER" or not self.drag_start_pos:
            return # Só no modo MOVER e se um drag foi iniciado

        # 1. Calcular Delta (mudança)
        # Delta (mudança) em coordenadas VISUAIS
        delta_x = event.x - self.drag_start_pos[0]
        delta_y = event.y - self.drag_start_pos[1]
        
        # Delta em coordenadas LÓGICAS (dividido pelo zoom)
        logical_delta_x = delta_x / self.zoom_level
        logical_delta_y = delta_y / self.zoom_level

        # 2. Se está fazendo um box-select (clicou no vazio)
        if self.selection_box_start:
            # 2a. Atualizar o retângulo visual
            start_x, start_y = self.selection_box_start
            self.canvas.coords(self.selection_box_id, start_x, start_y, event.x, event.y)
            
            # 2b. Converter caixa visual para lógica
            log_start_x, log_start_y = self._view_to_logical(start_x, start_y)
            log_end_x, log_end_y = self._view_to_logical(event.x, event.y)
            
            # Garante que x1 < x2 e y1 < y2 para a lógica de "dentro"
            log_box_x1 = min(log_start_x, log_end_x)
            log_box_y1 = min(log_start_y, log_end_y)
            log_box_x2 = max(log_start_x, log_end_x)
            log_box_y2 = max(log_start_y, log_end_y)

            # 2c. Recalcular o grupo de seleção (mas não mover ainda)
            self.selection_group.clear()
            for nome, (sx, sy) in self.positions.items():
                if (log_box_x1 <= sx <= log_box_x2) and (log_box_y1 <= sy <= log_box_y2):
                    self.selection_group.add(nome)

        # 3. Mover *todos* os estados no grupo de seleção
        # (Se for drag-de-estado-único, o grupo só tem 1 item)
        # (Se for box-select, o grupo tem N itens, e eles são movidos *enquanto* a caixa é desenhada)
        for nome in self.selection_group:
            # Evita erro se o estado foi deletado ou renomeado no meio do drag
            if nome in self.positions:
                old_log_x, old_log_y = self.positions[nome]
                self.positions[nome] = (old_log_x + logical_delta_x, old_log_y + logical_delta_y)

        # 4. Atualizar o ponto de início do drag para o próximo evento
        self.drag_start_pos = (event.x, event.y)
        
        self.desenhar_automato() # Redesenha

    def soltar_canvas(self, event):
        """Finaliza o arraste do estado ou da seleção."""
        # Reseta os estados de drag/seleção
        self.estado_movendo = None
        self.drag_start_pos = None
        self.selection_box_start = None # Importante
        
        if self.selection_box_id:
            self.canvas.delete(self.selection_box_id)
            self.selection_box_id = None
        
        # Não limpe o self.selection_group. Ele persiste até o próximo clique.
        
        self.desenhar_automato() # Redesenha no estado final

    def _editar_label_transicao(self, origem, destino):
        """Abre um diálogo para editar os símbolos de uma transição (exceto AP, Mealy, Turing)."""
        tipo = self.tipo_automato.get()
        if tipo in ["AP", "Mealy", "Turing"]:
            messagebox.showinfo("Editar Transição", f"Edição de transições {tipo} não implementada com duplo clique. Use Deletar e Criar.", parent=self.master)
            return

        simbolos_atuais = set()
        agrupado = self._agrupar_transicoes()
        if origem in agrupado and destino in agrupado[origem]:
            # Pega o label "bruto" (com 'e' em vez de 'ε')
            simbolos_brutos = set()
            if tipo in ["AFD", "AFN", "Moore"]:
                 for (o, s), dests in self.automato.transicoes.items():
                     dests_set = dests if isinstance(dests, set) else {dests}
                     if o == origem and destino in dests_set:
                         simbolos_brutos.add(s)
            
            simbolos_atuais = {s.replace(EPSILON, "e") for s in simbolos_brutos}

        label_atual = ",".join(sorted(list(simbolos_atuais)))

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
        """Abre o diálogo apropriado para criar uma transição entre dois estados."""
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


    def _get_estado_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão dentro de algum estado desenhado.
            NOTA: Recebe coordenadas LÓGICAS."""
        for nome, (sx, sy) in self.positions.items():
            # Calcula a distância do clique ao centro do estado (em coords lógicas)
            if (sx - x)**2 + (sy - y)**2 <= (STATE_RADIUS + 2)**2: # Usa raio lógico
                if nome in self.automato.estados: return self.automato.estados[nome]
        return None

    def _get_transicao_label_em(self, x, y):
        """Verifica se as coordenadas (x, y) estão sobre alguma label de transição.
            NOTA: Recebe coordenadas VISUAIS (event.x, event.y)."""
        # Pega todos os itens do canvas na área do clique (visual)
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        # Itera de trás para frente (itens desenhados por último ficam na frente)
        for item_id in reversed(items):
            tags = self.canvas.gettags(item_id)
            # Se o item tem a tag 'transition_label'
            if "transition_label_text" in tags: # Modificado: checa o texto, não o hitbox
                # Procura por uma tag no formato 'label_origem_destino'
                for tag in tags:
                    if tag.startswith("label_"):
                        parts = tag.split('_')
                        if len(parts) == 3: return parts[1], parts[2] # Retorna (origem, destino)
        return None

    # --- FUNÇÕES DE DESENHO (MODIFICADAS PARA ZOOM) ---
    def desenhar_automato(self, estados_ativos=None, transicoes_ativas=None, extra_info_str=None):
            """Desenha o autômato completo no canvas, destacando estados/transições ativas."""
            try:
                self.canvas.delete("all") # Limpa o canvas
                self.label_hitboxes.clear() # Limpa áreas clicáveis das labels
                transicoes_ativas = transicoes_ativas or set()
                agrupado = self._agrupar_transicoes() # Agrupa transições com formato JFLAP
                pares_processados = set() # Para evitar desenhar transições duplas duas vezes
                tipo = self.tipo_automato.get()

                # --- MUDANÇA: Pega o tema atual (0 para Light, 1 para Dark) ---
                current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1

                # --- VALORES COM ZOOM ---
                scaled_radius = STATE_RADIUS * self.zoom_level
                scaled_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)))
                bold_scaled_font = (FONT[0], max(1, int(FONT[1] * self.zoom_level)), "bold")
                
                # --- DESENHAR TRANSIÇÕES ---
                for origem_nome, destino_info in agrupado.items():
                    if origem_nome not in self.automato.estados or origem_nome not in self.positions: continue
                    origem = self.automato.estados[origem_nome]
                    
                    # Converte para Coords Visuais
                    x1, y1 = self._logical_to_view(*self.positions[origem_nome])

                    for destino_nome, simbolos in destino_info.items():
                        if destino_nome not in self.automato.estados or destino_nome not in self.positions: continue
                        destino = self.automato.estados[destino_nome]
                        
                        # Converte para Coords Visuais
                        x2, y2 = self._logical_to_view(*self.positions[destino_nome])
                        
                        par = tuple(sorted((origem_nome, destino_nome)))

                        # --- MUDANÇA: Seleciona cor da tupla ---
                        cor_linha = self.canvas_transicao_ativa[current_theme] if (origem_nome, destino_nome) in transicoes_ativas else self.canvas_fg_color[current_theme]
                        largura = 2.5 if (origem_nome, destino_nome) in transicoes_ativas else 1.5
                        
                        label_exibicao = "\n".join(sorted(list(simbolos))) 
                        label_tag = f"label_{origem_nome}_{destino_nome}"

                        transicao_font = bold_scaled_font
                        transicao_color = self.canvas_fg_color[current_theme] # MUDANÇA

                        if origem_nome == destino_nome: # Loop
                            text_id = self.canvas.create_text(
                                x1, y1 - (75 * self.zoom_level), # Posição Y com zoom
                                text=label_exibicao,
                                fill=transicao_color, 
                                font=transicao_font,  # Fonte com zoom
                                anchor=tk.CENTER,
                                tags=("transition_label_text", label_tag)
                            )
                            # Desenha o arco do loop (tudo com zoom)
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
                            
                            # --- MUDANÇA: Seleciona cor da tupla ---
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
                                text_x, text_y,
                                text=label_exibicao,
                                fill=transicao_color, 
                                font=transicao_font,
                                anchor=tk.CENTER,
                                tags=("transition_label_text", label_tag)
                            )
                            bbox = self.canvas.bbox(text_id)
                            if bbox: self.label_hitboxes[label_tag] = bbox

                # --- DESENHAR ESTADOS ---
                for nome, estado in self.automato.estados.items():
                    if nome not in self.positions: continue
                    
                    x, y = self._logical_to_view(*self.positions[nome])
                    
                    # --- LÓGICA DE COR MODIFICADA ---
                    cor_borda_padrao = self.canvas_fg_color[current_theme]

                    if estados_ativos and nome in estados_ativos:
                        cor_borda = self.canvas_estado_ativo[current_theme] # Vermelho (simulação)
                    
                    # --- MODIFICAÇÃO AQUI ---
                    elif self.origem_transicao and nome == self.origem_transicao.nome:
                        cor_borda = self.cor_selecao_grupo[current_theme] # Azul (origem da transição)
                    # --- FIM DA MODIFICAÇÃO ---
                    
                    elif nome in self.selection_group:
                        cor_borda = self.cor_selecao_grupo[current_theme] # Azul (selecionado)
                    else:
                        cor_borda = cor_borda_padrao
                    # --- FIM DA MODIFICAÇÃO ---
                    
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
                # O destaque verde tracejado foi removido para usar o azul sólido acima
                # if self.origem_transicao and self.origem_transicao.nome in self.positions:
                #     x, y = self._logical_to_view(*self.positions[self.origem_transicao.nome])
                #     self.canvas.create_oval(x-scaled_radius-3, y-scaled_radius-3, x+scaled_radius+3, y+scaled_radius+3,
                #                             outline=self.cor_verde_fg[current_theme], width=2, dash=(4, 4), # MUDANÇA
                #                             tags="origem_transicao_destaque")

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
            
            # --- MUDANÇA: Pega o tema atual (0 para Light, 1 para Dark) ---
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
                text_x, text_y,
                text=label_empilhada,
                fill=transicao_color,
                font=transicao_font,
                anchor=tk.CENTER,
                tags=("transition_label_text", label_tag)
            )

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

    # --- FUNÇÕES DE SIMULAÇÃO ---
    def iniciar_simulacao(self):
        """Inicia a simulação passo a passo do autômato com a cadeia de entrada."""
        self.parar_simulacao(final_state=False) # Reseta simulação anterior
        cadeia = self.entrada_cadeia.get()
        tipo = self.tipo_automato.get()
        current_theme = 0 if ctk.get_appearance_mode() == "Light" else 1 # NOVO

        # Limpa labels de status
        self.lbl_cadeia_consumida.configure(text="")
        self.lbl_cadeia_restante.configure(text=cadeia if tipo not in ["Turing"] else "", text_color=self.default_fg_color[current_theme])
        self.lbl_output_valor.configure(text="")
        self.lbl_tape_valor.configure(text="" if tipo == "Turing" else "")

        try:
            # Validações básicas
            if not self.automato.estados: raise ValueError("O autômato está vazio.")
            if not self.automato.estado_inicial:
                if self.automato.estados:
                    first_state_name = next(iter(self.automato.estados))
                    print(f"Aviso: Estado inicial não definido. Usando '{first_state_name}' como inicial.")
                    self.automato.definir_estado_inicial(first_state_name)
                    self.desenhar_automato() 
                else: raise ValueError("Estado inicial não definido e autômato vazio.")

            # Instancia o simulador correto
            if tipo == "AFD": self.simulador = SimuladorAFD(self.automato, cadeia)
            elif tipo == "AFN": self.simulador = SimuladorAFN(self.automato, cadeia)
            elif tipo == "AP": self.simulador = SimuladorAP(self.automato, cadeia)
            elif tipo == "Moore": self.simulador = SimuladorMoore(self.automato, cadeia)
            elif tipo == "Mealy": self.simulador = SimuladorMealy(self.automato, cadeia)
            elif tipo == "Turing": self.simulador = SimuladorMT(self.automato, cadeia)

        except Exception as e: 
            messagebox.showerror("Erro ao Iniciar", str(e)); return

        # Atualiza a UI para o modo de simulação
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

        # Se não há mais passos (simulação terminou)
        if not passo_info:
            current_status_text = self.lbl_status_simulacao.cget("text")
            if current_status_text == "Simulando..." or current_status_text == "Status: Aguardando":
                aceitou = False
                try: 
                    # Tenta obter o último estado do gerador (pode falhar se já fechado)
                    last_step_vars = self.simulador.gerador.gi_frame.f_locals
                    last_active_states_raw = last_step_vars.get('estado_atual', last_step_vars.get('estados_atuais', set()))
                    # Garante que é um conjunto de strings
                    if isinstance(last_active_states_raw, str):
                        last_active_states = {last_active_states_raw}
                    elif isinstance(last_active_states_raw, set):
                        last_active_states = last_active_states_raw
                    else:
                        last_active_states = set()

                    if last_active_states and hasattr(self.simulador, 'automato') and self.simulador.automato.estados_finais:
                        aceitou = any(e in self.simulador.automato.estados_finais
                                      for e in last_active_states if e in self.simulador.automato.estados)
                except Exception as e:
                    print(f"Erro ao verificar estado final: {e}")

                # Atualiza o status final (Aceita/Não Aceita)
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

        # Processa as informações do passo atual
        status = passo_info["status"]
        extra_info_canvas = None 

        if "tape" in passo_info and passo_info["tape"] is not None:
            self.lbl_tape_valor.configure(text=passo_info["tape"])
            extra_info_canvas = passo_info["tape"]
        if "output" in passo_info and passo_info["output"] is not None:
            self.lbl_output_valor.configure(text=passo_info["output"])
        if "pilha" in passo_info and passo_info["pilha"] is not None:
                extra_info_canvas = passo_info["pilha"]

        # --- BLOCO MODIFICADO ---
        if "cadeia_restante" in passo_info and tipo != "Turing":
            cadeia_restante = passo_info['cadeia_restante']
            cadeia_original = self.entrada_cadeia.get()
            split_point = len(cadeia_original) - len(cadeia_restante)
            cadeia_consumida = cadeia_original[:split_point]
            
            # Define a cor com base no status ATUAL
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
        # --- FIM DO BLOCO MODIFICADO ---

        # Atualiza o canvas e status com base no resultado do passo
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
            
            # A cor da lbl_cadeia_consumida E lbl_cadeia_restante
            # já foi definida como vermelha no bloco 'if "cadeia_restante"...' acima.

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
        """Abre um arquivo .jff e carrega o autômato no simulador."""
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("JFLAP files", "*.jff"), ("All files", "*.*")],
                title="Abrir Arquivo JFF",
                parent=self.master
            )
            if not filepath:
                return # Usuário cancelou

            tree = ET.parse(filepath)
            root = tree.getroot()

            # 1. Obter o tipo de autômato
            jflap_type_node = root.find("type")
            if jflap_type_node is None:
                raise ValueError("Arquivo JFF inválido: tag <type> não encontrada.")
            jflap_type = jflap_type_node.text.lower()
            
            automaton_node = root.find("automaton")
            if automaton_node is None:
                raise ValueError("Arquivo JFF inválido: tag <automaton> não encontrada.")

            # Mapeia o tipo JFLAP para o tipo do nosso simulador
            tipo_simulador = ""
            if jflap_type == "fa":
                tipo_simulador = "AFD" # Padrão, verificaremos AFN depois
            elif jflap_type == "pda":
                tipo_simulador = "AP"
            elif jflap_type == "turing":
                tipo_simulador = "Turing"
            elif jflap_type == "mealy":
                if automaton_node.find("state/output") is not None:
                        tipo_simulador = "Moore"
                else:
                        tipo_simulador = "Mealy"
            else:
                raise ValueError(f"Tipo de autômato JFLAP '{jflap_type}' não suportado.")

            # 2. Limpar a tela e configurar o novo tipo de autômato
            self.tipo_automato.set(tipo_simulador)
            self.mudar_tipo_automato() 

            # 3. Mapear IDs de estado para nomes (JFLAP usa IDs)
            id_to_name = {}
            states_nodes = automaton_node.findall("state")
            
            state_data_map = {} 
            self.contador_estados = 0 

            for state in states_nodes:
                state_id = state.get("id")
                state_name = state.get("name")
                if not state_name:
                    state_name = f"q{self.contador_estados}"
                while state_name in self.automato.estados or state_name in (d['name'] for d in state_data_map.values()):
                        self.contador_estados += 1
                        state_name = f"q{self.contador_estados}"

                id_to_name[state_id] = state_name
                
                x_node = state.find("x")
                y_node = state.find("y")
                x_pos = float(x_node.text) if x_node is not None and x_node.text else (50.0 + int(state_id) * 80)
                y_pos = float(y_node.text) if y_node is not None and y_node.text else 50.0
                
                state_data_map[state_id] = {
                    'name': state_name,
                    'x': x_pos,
                    'y': y_pos,
                    'is_initial': state.find("initial") is not None,
                    'is_final': state.find("final") is not None,
                    'output': state.find("output").text if state.find("output") is not None else ""
                }

            # 4. Adicionar Estados
            for state_id, data in state_data_map.items():
                self.positions[data['name']] = (data['x'], data['y'])
                output_val = data['output'] if tipo_simulador == "Moore" else ""
                
                if tipo_simulador == "Moore":
                        self.automato.adicionar_estado(data['name'], data['x'], data['y'], output=output_val)
                else:
                        self.automato.adicionar_estado(data['name'], data['x'], data['y'])

            # 5. Definir estados Iniciais e Finais
            for state_id, data in state_data_map.items():
                    if data['is_initial']:
                        self.automato.definir_estado_inicial(data['name'])
                    if data['is_final']:
                        # Use o método do automato para *adicionar* um estado final
                        if hasattr(self.automato, 'adicionar_estado_final'):
                            self.automato.adicionar_estado_final(data['name'])
                        else: # Fallback para o método de alternar
                            self.automato.alternar_estado_final(data['name'])


            # 6. Adicionar Transições
            transition_nodes = automaton_node.findall("transition")
            
            if tipo_simulador == "AFD":
                transitions_check = {}
                is_afn = False
                for trans in transition_nodes:
                    from_id = trans.find("from").text
                    read_node = trans.find("read")
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    chave = (from_id, simbolo)
                    
                    if chave in transitions_check:
                        is_afn = True 
                        break
                    transitions_check[chave] = True
                    if simbolo == EPSILON:
                        is_afn = True
                        break
                
                if is_afn:
                    print("Autômato 'fa' detectado como AFN. Recarregando como AFN.")
                    tipo_simulador = "AFN"
                    self.tipo_automato.set("AFN")
                    self.mudar_tipo_automato()
                    for state_id, data in state_data_map.items():
                        self.positions[data['name']] = (data['x'], data['y'])
                        self.automato.adicionar_estado(data['name'], data['x'], data['y'])
                    for state_id, data in state_data_map.items():
                            if data['is_initial']:
                                self.automato.definir_estado_inicial(data['name'])
                            if data['is_final']:
                                # Use o método do automato para *adicionar* um estado final
                                if hasattr(self.automato, 'adicionar_estado_final'):
                                    self.automato.adicionar_estado_final(data['name'])
                                else: # Fallback para o método de alternar
                                    self.automato.alternar_estado_final(data['name'])

            # Processa as transições
            for trans in transition_nodes:
                from_name = id_to_name.get(trans.find("from").text)
                to_name = id_to_name.get(trans.find("to").text)
                if not from_name or not to_name:
                    continue 

                if tipo_simulador in ["AFD", "AFN", "Moore"]:
                    read_node = trans.find("read")
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    self.automato.adicionar_transicao(from_name, simbolo, to_name)
                
                elif tipo_simulador == "AP":
                    read_node = trans.find("read")
                    pop_node = trans.find("pop")
                    push_node = trans.find("push")
                    
                    s_in = EPSILON if read_node is None or read_node.text is None else read_node.text
                    s_pop = EPSILON if pop_node is None or pop_node.text is None else pop_node.text
                    s_push = EPSILON if push_node is None or push_node.text is None else push_node.text
                    
                    self.automato.adicionar_transicao(from_name, s_in, s_pop, to_name, s_push)
                
                elif tipo_simulador == "Mealy":
                    read_node = trans.find("read")
                    transout_node = trans.find("transout")
                    
                    simbolo = EPSILON if read_node is None or read_node.text is None else read_node.text
                    output = EPSILON if transout_node is None or transout_node.text is None else transout_node.text
                    
                    self.automato.adicionar_transicao(from_name, simbolo, to_name, output)

                elif tipo_simulador == "Turing":
                    read_node = trans.find("read")
                    write_node = trans.find("write")
                    move_node = trans.find("move")
                    
                    simbolo_branco_auto = self.automato.simbolo_branco
                    lido = simbolo_branco_auto if read_node is None or read_node.text is None else read_node.text
                    escrito = simbolo_branco_auto if write_node is None or write_node.text is None else write_node.text
                    direcao = move_node.text if move_node is not None else "R"
                    
                    self.automato.adicionar_transicao(from_name, lido, to_name, escrito, direcao)

            # 7. Redesenhar o canvas
            self.zoom_slider.set(1.0) # Reseta o zoom para 100% ao abrir
            self.desenhar_automato()
            messagebox.showinfo("Importar JFF", f"Autômato carregado com sucesso de:\n{filepath}", parent=self.master)

        except ET.ParseError:
            messagebox.showerror("Erro ao Importar JFF", "O arquivo selecionado não é um XML válido.", parent=self.master)
            self.limpar_tela() 
        except Exception as e:
            messagebox.showerror("Erro ao Importar JFF", f"Ocorreu um erro ao processar o arquivo:\n{e}", parent=self.master)
            self.limpar_tela() 


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

            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            margin = 2 
            img = ImageGrab.grab(bbox=(x + margin, y + margin, x1 - margin, y1 - margin))
            img.save(filepath, "JPEG") 
            messagebox.showinfo("Exportar JPG", f"Autômato salvo como JPG em:\n{filepath}", parent=self.master)
        except Exception as e: 
            messagebox.showerror("Erro ao Exportar JPG", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JPG: {e}")


    def exportar_para_jff(self):
        """Converte o autômato atual para o formato JFLAP (.jff) e salva em arquivo."""
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
                if estado.is_inicial:
                    ET.SubElement(state_element, "initial")
                if estado.is_final:
                    ET.SubElement(state_element, "final")
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

            # Formata o XML
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml_str = dom.toprettyxml(indent="  ")

            # Salva o XML
            with open(filepath, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                f.write(pretty_xml_str.split('\n', 1)[1])

            messagebox.showinfo("Exportar JFF", f"Autômato salvo como JFF em:\n{filepath}", parent=self.master)

        except Exception as e: 
            messagebox.showerror("Erro ao Exportar JFF", f"Ocorreu um erro:\n{e}", parent=self.master)
            print(f"Erro ao exportar JFF: {e}")


# --- CLASSES DE DIÁLOGO ---
# Diálogos modais para inserir informações de transição

class TransicaoPilhaDialog(ctk.CTkToplevel):
    """Diálogo para criar/editar transições de Autômato de Pilha."""
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
        simbolo_input = self.e_simbolo.get()
        output_input = self.e_output.get()
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
        self.e_lido.insert(0, '☐') 

        ctk.CTkLabel(self, text="Símbolo Escrito:").pack(padx=20, pady=(10,0))
        self.e_escrito = ctk.CTkEntry(self, **style_dict)
        self.e_escrito.pack(padx=20, pady=5)
        self.e_escrito.insert(0, '☐')

        ctk.CTkLabel(self, text="Direção (L/R):").pack(padx=20, pady=(10,0))
        self.e_dir = ctk.CTkEntry(self, width=50, **style_dict) 
        self.e_dir.pack(padx=20, pady=5)
        self.e_dir.insert(0, 'R') 

        ctk.CTkButton(self, text="OK", command=self.ok, **style_dict).pack(padx=20, pady=20)

        self.grab_set()
        self.e_lido.focus()

    def ok(self):
        """Valida e processa os dados da transição de Turing."""
        lido = self.e_lido.get() or '☐' 
        escrito = self.e_escrito.get() or '☐'
        direcao = (self.e_dir.get() or 'R').upper() 

        if direcao not in ['L', 'R']:
            messagebox.showerror("Erro", "Direção deve ser 'L' ou 'R'.", parent=self)
            return
        if len(lido) > 1 or len(escrito) > 1:
                messagebox.showerror("Erro", "Símbolos da fita devem ter apenas 1 caractere.", parent=self)
                return

        self.resultado = {'lido': lido, 'escrito': escrito, 'dir': direcao}
        self.destroy()