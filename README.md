# Simulador de Autômatos Visual

Projeto acadêmico desenvolvido para a disciplina de Linguagens Formais e Autômatos, oferecendo uma interface gráfica para a criação, visualização e simulação de diversos modelos de autômatos.

## Visão Geral

Este software permite que estudantes e entusiastas de teoria da computação desenhem autômatos visualmente, executem simulações passo a passo com cadeias de entrada e validem suas construções. A interface suporta os principais tipos de máquinas estudados na disciplina, desde autômatos finitos simples até Máquinas de Turing.

## Funcionalidades

* **Ampla Compatibilidade de Modelos**: Suporte para os seguintes autômatos:
    * Autômato Finito Determinístico (AFD)
    * Autômato Finito Não Determinístico (AFN)
    * Autômato de Pilha (AP)
    * Máquina de Moore
    * Máquina de Mealy
    * Máquina de Turing (fita única, determinística)
* **Editor Visual**: Interface de "arrastar e soltar" para:
    * Criar, renomear e deletar estados.
    * Definir estados iniciais e finais.
    * Criar transições entre estados com os rótulos apropriados para cada tipo de máquina.
    * Mover estados e grupos de estados no canvas.
* **Simulação Passo a Passo**:
    * Insira uma cadeia de entrada e execute a simulação passo a passo.
    * Visualize o estado atual, a cadeia restante, o conteúdo da pilha (para AP) ou a saída (para Moore/Mealy).
    * Acompanhe a fita da Máquina de Turing em tempo real.
* **Importação e Exportação**:
    * Compatibilidade total com o formato de arquivo `.jff` do JFLAP para importar e exportar autômatos.
    * Exporte a visualização atual do canvas para uma imagem `.jpg`.
* **Personalização**:
    * Suporte a temas claro (Light) e escuro (Dark).
    * Controle de zoom no canvas.

## Estrutura do Projeto

O código-fonte está organizado nos seguintes pacotes principais:

* **`/automato`**: Contém as definições de classes e a lógica de dados para cada tipo de autômato (ex: `automato_finito.py`, `automato_pilha.py`).
* **`/simulador`**: Contém a lógica de execução para cada tipo de simulação passo a passo (ex: `simulador_passos.py`).
* **`/gui`**: Contém os arquivos da interface gráfica de usuário (GUI) construída com CustomTkinter (ex: `tela_principal.py`, `tela_menu.py`).
* **`/assets`**: Contém recursos estáticos, como imagens e ícones.
* **`main.py`**: Ponto de entrada principal da aplicação.

## Instalação e Execução

Para executar o projeto localmente, siga estes passos:

1.  **Clone o repositório:**
    ```sh
    git clone https://[URL-DO-SEU-REPOSITORIO]
    cd projetoLfa2025.2
    ```

2.  **Crie um ambiente virtual (Recomendado):**
    ```sh
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação:**
    ```sh
    python main.py
    ```

## Créditos

Este projeto foi desenvolvido por:

* **Desenvolvimento:**
    * Arthur Carvalho
    * Ana Letícia

* **Idealização:**
    * Leandro Dias
