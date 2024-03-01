from Figuras import Circulo
from Figuras import Cuadrado
from Prueba import  Tarjeta

redondo=Circulo(6)
print(redondo.areas())
print(redondo)

circuloDos=Circulo(6)

if circuloDos==redondo:
    print("Iguales")
else:
    print("No iguales")