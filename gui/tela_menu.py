import customtkinter as ctk
from tkinter import messagebox

class TelaMenu:
    def __init__(self, master, iniciar_callback):
        self.master = master
        self.iniciar_callback = iniciar_callback
        
        # Frame principal centralizado com visual moderno
        self.frame_menu = ctk.CTkFrame(master, corner_radius=20, fg_color=("gray85", "gray20"))
        self.frame_menu.place(relx=0.5, rely=0.5, anchor="center")
        
        # Título principal com estilo
        titulo = ctk.CTkLabel(
            self.frame_menu, 
            text="Simulador de Autômatos do IC", 
            font=ctk.CTkFont(size=30, weight="bold")
        )
        titulo.pack(padx=70, pady=(50, 10))
        
        # Subtítulo
        subtitulo = ctk.CTkLabel(
            self.frame_menu,
            text="AFD • AFN • AP • Moore • Mealy • Turing",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60")
        )
        subtitulo.pack(padx=70, pady=(0, 40))
        
        # Botão Iniciar
        btn_iniciar = ctk.CTkButton(
            self.frame_menu,
            text="▶  Iniciar",
            command=self.iniciar,
            width=240,
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=("#4CAF50", "#388E3C"),
            hover_color=("#388E3C", "#2E7D32")
        )
        btn_iniciar.pack(padx=50, pady=12)
        
        # Botão Créditos
        btn_creditos = ctk.CTkButton(
            self.frame_menu,
            text="ℹ️  Créditos",
            command=self.mostrar_creditos,
            width=240,
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=("#2196F3", "#1976D2"),
            hover_color=("#1976D2", "#1565C0")
        )
        btn_creditos.pack(padx=50, pady=12)
        
        # Botão Sair
        btn_sair = ctk.CTkButton(
            self.frame_menu,
            text="✕  Sair",
            command=self.sair,
            width=240,
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        btn_sair.pack(padx=50, pady=(12, 50))
    
    def iniciar(self):
        """Destroi o menu e inicia o simulador"""
        self.frame_menu.destroy()
        self.iniciar_callback()
    
    def mostrar_creditos(self):
        """Exibe a janela de créditos"""
        janela_creditos = ctk.CTkToplevel(self.master)
        janela_creditos.title("Créditos")
        janela_creditos.geometry("450x350")
        janela_creditos.resizable(False, False)
        
        # Centraliza a janela
        janela_creditos.transient(self.master)
        janela_creditos.grab_set()
        
        # Frame de conteúdo
        frame_conteudo = ctk.CTkFrame(janela_creditos, corner_radius=15)
        frame_conteudo.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título Créditos com ícone
        ctk.CTkLabel(
            frame_conteudo,
            text="Créditos",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(25, 15))
        
        # Separador
        separator1 = ctk.CTkFrame(frame_conteudo, height=2, fg_color=("gray70", "gray30"))
        separator1.pack(fill="x", padx=40, pady=15)
        
        # Feito por
        ctk.CTkLabel(
            frame_conteudo,
            text="Feito por:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#2196F3", "#64B5F6")
        ).pack(pady=(5, 8))
        
        ctk.CTkLabel(
            frame_conteudo,
            text="Arthur Carvalho",
            font=ctk.CTkFont(size=15)
        ).pack(pady=3)
        
        ctk.CTkLabel(
            frame_conteudo,
            text="Ana Letícia",
            font=ctk.CTkFont(size=15)
        ).pack(pady=3)
        
        # Separador
        separator2 = ctk.CTkFrame(frame_conteudo, height=2, fg_color=("gray70", "gray30"))
        separator2.pack(fill="x", padx=40, pady=15)
        
        # Idealizado por
        ctk.CTkLabel(
            frame_conteudo,
            text="Idealizado por:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#4CAF50", "#81C784")
        ).pack(pady=(5, 8))
        
        ctk.CTkLabel(
            frame_conteudo,
            text="Leandro Dias",
            font=ctk.CTkFont(size=15)
        ).pack(pady=3)
        
        # Botão Fechar
        ctk.CTkButton(
            frame_conteudo,
            text="Fechar",
            command=janela_creditos.destroy,
            width=140,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(25, 15))
    
    def sair(self):
        """Fecha o aplicativo"""
        self.master.quit()