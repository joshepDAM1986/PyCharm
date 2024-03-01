from Producto import Producto


class Perecedero(Producto):
    def __init__(self, nombre, identificador, precio, dias_para_caducar):
        super().__init__(nombre, identificador, precio)
        self.dias_para_caducar = dias_para_caducar

    def comprar(self, unidades):
        if self.dias_para_caducar == 1:
            precio_final = super().comprar(unidades) * 0.25
        elif self.dias_para_caducar == 2:
            precio_final = super().comprar(unidades) * 0.33
        elif self.dias_para_caducar == 3:
            precio_final = super().comprar(unidades) * 0.5
        else:
            precio_final = super().comprar(unidades)
        return precio_final

    def __str__(self):
        return f"Perecedero: {self.nombre}\nIdentificador: {self.identificador}\nPrecio: ${self.precio}\nDías para caducar: {self.dias_para_caducar}"


class Tienda:
    def __init__(self):
        self.lista_productos = []

    def nuevo_producto(self, producto):
        self.lista_productos.append(producto)

    def __str__(self):
        resumen = ""
        for producto in self.lista_productos:
            resumen += str(producto) + "\n\n"
        return resumen

tienda = Tienda()

producto1 = Producto("Laptop", "P1", 1000)
perecedero1 = Perecedero("Leche", "P2", 2, 1)

tienda.nuevo_producto(producto1)
tienda.nuevo_producto(perecedero1)

print(tienda)