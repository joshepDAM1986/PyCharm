# EJERCICIO 4
# Crear la clase Joya que tiene los siguientes atributos:
# - Código de identificación (alfanumérico)
# - Nombre.
# - Marca.
# - Tipo (collar, anillo, brazalete, diadema o broche).
# - Precio.
# - Peso en gramos.
# - Quilates.
# Además de los siguientes métodos:
# - Constructor con todos los parámetros menos el id que tiene el prefijo JOYA-X , donde X es un número que se controla
# desde la clase y que se incrementa en 1 cada vez que se crea una instancia de la clase Joya.
# - Método __eq__ donde una joya es igual a otra si coinciden los códigos identificativos.
# - Método __str__.
# - Método pureza() que devuelve un número con la pureza de oro en función del peso y los quilates
# (1quilate=aprox 4,167% de oro)

class Joya:
    contador= 0

    def __init__(self, nombre, marca, tipo, precio, peso, quilates):
        Joya.contador+= 1
        self.codigo= f'JOYA-{Joya.contador}'

        self.nombre = nombre
        self.marca = marca
        self.tipo = tipo
        self.precio = precio
        self.peso = peso
        self.quilates = quilates

    def __eq__(self, other):
        return self.codigo== other.codigo

    def __str__(self):
        return f"Código: {self.codigo}\nNombre: {self.nombre}\nMarca: {self.marca}\n" \
               f"Tipo: {self.tipo}\nPrecio: ${self.precio}\nPeso en gramos: {self.peso}g\nQuilates: {self.quilates}"

    def pureza(self):
        pureza_oro = (self.quilates * 4.167) / (self.peso/ 100)
        return pureza_oro


joya1 = Joya("Collar de Diamantes", "Luxury Jewelry", "collar", 5000, 20, 18)
joya2 = Joya("Anillo de Zafiro", "Elegance Rings", "anillo", 3000, 10, 14)

print(joya1)
print("\nPureza de oro:", joya1.pureza(), "%\n")

print(joya2)
print("\nPureza de oro:", joya2.pureza(), "%\n")

if joya1 == joya2:
    print("Las joyas son iguales.")
else:
    print("Las joyas son diferentes.")
