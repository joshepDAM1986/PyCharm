# EJERCICIO 7
# Crear la clase Producto que tiene los atributos nombre, identificador (código alfanumérico) y precio.
# Tiene que tener constructor, __str__ y __eq__, donde un producto es igual a otro cuando tienen el mismo
# identificador. También tendrá el método comprar que tiene como parámetro las unidades a llevarse.
# El método comprar devuelve un float con el precio multiplicado por la unidades que se quiere llevar.
# Si al comprar se lleva más de 50 unidades el precio final se reduce a la mitad.
# Crear la clase Perecedero que hereda de Producto. Se añade un atributo más que es los días para caducar.
# Hay que hacer el método __str__. El método comprar es similar al de producto solo que le reduce el precio
# calculado en la clase Producto según los días que le queden para caducar:
# - Si le queda un día para caducar, el precio final es la cuarta parte del que devuelve comprar de la
# clase Producto.
# - Si le quedan 2 días para caducar, el precio final es la tercera parte.
# - Si le quedan 3 días para caducar, el precio final es la mitad.

class Producto:
    def __init__(self, nombre, identificador, precio):
        self.nombre = nombre
        self.identificador = identificador
        self.precio = precio

    def __eq__(self, other):
        return self.identificador == other.identificador

    def comprar(self, unidades):
        if unidades > 50:
            precio_final = self.precio * unidades * 0.5
        else:
            precio_final = self.precio * unidades
        return precio_final

    def __str__(self):
        return f"Producto: {self.nombre}\nIdentificador: {self.identificador}\nPrecio: ${self.precio}"

