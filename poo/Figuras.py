class Circulo:
    pi=3.141592
    def __init__(self,radio):
        self._radio=radio
    def __str__(self):
        return f"El circulo tiene {self._radio} metros de radio"
    def areas(self):
        return Circulo.pi*self._radio**2

    def __eq__(self, otro):
        return self._radio==otro._radio

class Cuadrado:
    def __init__(self,lado):
        self._lado=lado