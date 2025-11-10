import customtkinter as ctk
from tkinter import messagebox
from PIL import Image # Necessário para carregar a imagem
import os # Necessário para construir o caminho absoluto

class TelaMenu:
    def __init__(self, master, iniciar_callback):
        self.master = master
        self.iniciar_callback = iniciar_callback

        # Frame principal centralizado com visual moderno
        self.frame_menu = ctk.CTkFrame(master, corner_radius=20, fg_color=("gray85", "gray20"))
        self.frame_menu.place(relx=0.5, rely=0.5, anchor="center")

        # --- NOVO: Carregar e exibir o logo do simulador ---
        try:
            # Diretório onde este script (tela_menu.py) está localizado
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Navega um nível acima do diretório 'gui' para chegar à raiz do projeto
            base_dir = os.path.dirname(script_dir) 
            # Caminho para o logo.png
            logo_path = os.path.join(base_dir, "assets", "images", "logo.png")

            if not os.path.exists(logo_path):
                 raise FileNotFoundError(f"Logo não encontrado em: {logo_path}")

            logo_image = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(200, 200) # Ajuste o tamanho conforme necessário
            )
            logo_label = ctk.CTkLabel(self.frame_menu, image=logo_image, text="")
            # Adiciona padding acima do logo e um pouco abaixo
            logo_label.pack(pady=(40, 10)) 

        except Exception as e:
            print(f"Erro ao carregar logo.png: {e}")
            # Se falhar, apenas continua sem o logo
            pass
        # --- FIM NOVO ---

        # Título principal com estilo
        titulo = ctk.CTkLabel(
            self.frame_menu,
            text="Simulador de Autômatos do IC",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        # Padding ajustado (era 50, 10)
        titulo.pack(padx=70, pady=(10, 10))

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
        janela_creditos.geometry("450x450") # Altura aumentada para o logo
        janela_creditos.resizable(False, False)

        janela_creditos.transient(self.master)
        janela_creditos.grab_set()

        frame_conteudo = ctk.CTkFrame(janela_creditos, corner_radius=15)
        frame_conteudo.pack(fill="both", expand=True, padx=15, pady=15)

        # --- CORREÇÃO: Construir caminho absoluto para a imagem ---
        try:
            # Diretório onde este script (tela_menu.py) está localizado
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Caminho relativo da imagem a partir da raiz do projeto (assumindo que assets está na raiz)
            # Navega um nível acima do diretório 'gui' para chegar à raiz do projeto
            base_dir = os.path.dirname(script_dir) # Vai para simulador_de_automatos/
            # Junta as partes para formar o caminho completo
            image_path = os.path.join(base_dir, "assets", "images", "logo_faculdade.png") # Monta o caminho completo

            # Verifica se o arquivo existe ANTES de tentar abrir
            if not os.path.exists(image_path):
                 raise FileNotFoundError(f"Imagem não encontrada em: {image_path}")

            # Carrega a imagem usando o caminho absoluto
            logo_image = ctk.CTkImage(
                light_image=Image.open(image_path),
                dark_image=Image.open(image_path), # Use a mesma ou outra para modo escuro
                size=(80, 80) # Ajuste o tamanho conforme necessário
            )
            # Cria um Label para exibir a imagem
            logo_label = ctk.CTkLabel(frame_conteudo, image=logo_image, text="")
            logo_label.pack(pady=(15, 5)) # Adiciona padding

        except FileNotFoundError as e:
             # Imprime o caminho que falhou para depuração
             print(f"Erro: {e}")
             ctk.CTkLabel(frame_conteudo, text="[Logo não encontrado]", text_color="gray").pack(pady=(15, 5))
        except Exception as e:
            # Imprime outros erros que possam ocorrer ao carregar a imagem (formato inválido, etc.)
            print(f"Erro ao carregar a imagem do logo: {e}")
            ctk.CTkLabel(frame_conteudo, text="[Erro ao carregar logo]", text_color="gray").pack(pady=(15, 5))
        # --- FIM DA CORREÇÃO ---


        # Título Créditos
        ctk.CTkLabel(
            frame_conteudo,
            text="Créditos",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(5, 10))

        # Separador 1
        separator1 = ctk.CTkFrame(frame_conteudo, height=2, fg_color=("gray70", "gray30"))
        separator1.pack(fill="x", padx=40, pady=10)

        # Feito por
        ctk.CTkLabel(
            frame_conteudo,
            text="Feito por:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#2196F3", "#64B5F6")
        ).pack(pady=(5, 5))

        ctk.CTkLabel(
            frame_conteudo,
            text="Arthur Carvalho",
            font=ctk.CTkFont(size=15)
        ).pack(pady=2)

        ctk.CTkLabel(
            frame_conteudo,
            text="Ana Letícia",
            font=ctk.CTkFont(size=15)
        ).pack(pady=2)

        # Separador 2
        separator2 = ctk.CTkFrame(frame_conteudo, height=2, fg_color=("gray70", "gray30"))
        separator2.pack(fill="x", padx=40, pady=10)

        # Idealizado por
        ctk.CTkLabel(
            frame_conteudo,
            text="Idealizado por:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#4CAF50", "#81C784")
        ).pack(pady=(5, 5))

        ctk.CTkLabel(
            frame_conteudo,
            text="Leandro Dias",
            font=ctk.CTkFont(size=15)
        ).pack(pady=2)

        # Botão Fechar
        ctk.CTkButton(
            frame_conteudo,
            text="Fechar",
            command=janela_creditos.destroy,
            width=140,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 10))

    def sair(self):
        """Fecha o aplicativo"""
        self.master.quit()