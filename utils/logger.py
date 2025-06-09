class Logger:
    def __init__(self, name="GlobalLogger"):
        self.name = name

    def log(self, message):
        print(f"[{self.name}] {message}")