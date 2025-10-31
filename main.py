import customtkinter as ctk
from gui.tela_menu import TelaMenu
from gui.tela_principal import TelaPrincipal

# --- Configuração da Aparência ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def criar_menu(): #Cria o menu inicial
    menu = TelaMenu(root, iniciar_simulador)

def iniciar_simulador(): #Função chamada quando o botão Iniciar é clicado
    app = TelaPrincipal(root, voltar_menu_callback=criar_menu)

if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Simulador de Autômatos Visual")
    root.geometry("1200x800")
    
    criar_menu()
    
    root.mainloop()