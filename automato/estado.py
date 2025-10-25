class Estado:
    def __init__(self, nome, x, y, is_final=False, is_inicial=False, output=""):
        self.nome = nome
        self.x = x
        self.y = y
        self.is_final = is_final
        self.is_inicial = is_inicial
        self.output = output # Usado pela Máquina de Moore

    def __repr__(self):
        return f"Estado({self.nome})"