# EJERCICIO 1
# Crear una clase Coche, a través de la cual se puedan crear objetos que almacenen el color del
# coche, la marca, el modelo, el número de caballos, el número de puertas y la matrícula. Crear el
# metodo __init__, el método __str__. Crear también el método __eq__ que compare cuando dos
# objetos son iguales (tienen la misma matricula).

class Coche:
    def __init__(self,color,marca,modelo,caballos,puertas,matricula):
        self.color=color
        self._marca=marca
        self.modelo=modelo
        self.caballos=caballos
        self.puertas=puertas
        self.matricula=matricula

    def __str__ (self):
        return f"El coche de la marca {self._marca}, modelo {self.modelo} tiene {self.caballos} y {self.puertas}, con matricula {self.matricula} es de color {self.color}"

    def __eq__(self,otro):
        return self.matricula==otro.matricula

coche1=Coche("rojo","Toyota","Auris",90,5,"HCT 2387")
print(coche1)

coche2 = Coche("blanco", "Toyota", "Auris", 90, 5, "HCT 2387")
coche3 = Coche("blanco", "Toyota", "Auris", 90, 5, "HCT 8723")

if coche2==coche3:
    print("Iguales")
else:
    print("No iguales")
