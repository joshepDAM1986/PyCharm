class Tarjeta:

    def __init__(self,numero,saldo=0): #Saldo por defecto 0
        self._numero=numero
        self.saldo=saldo
    def mostrar_saldo(self):
        print(f"La tarjeta {self._numero} tiene {self.saldo} €")

    def __str__(self):
        return f"La tarjeta {self._numero} tiene {self.saldo}€"

    def pagar(self, cantidad):
        if cantidad<=self.saldo:
            self.saldo-=cantidad

#Clase que hereda de la clase Tarjeta
class TarjetaDescuento(Tarjeta):
    def __init__(self,numero,descuento,saldo=0):
        super().__init__(numero,saldo)
        self._descuento = descuento
    def __str__(self):
        return f"{super().__str__()} y un descuento asociado de {self._descuento}"

    def pagar(self, cantidad):
        precioFinal= cantidad-cantidad*self._descuento/100
        super().pagar(precioFinal)


if __name__=="__main__":

    tarjeta_prueba=Tarjeta("ES123456789", 500)
    print(tarjeta_prueba)

    tarjeta_prueba.mostrar_saldo()
    # El saldo es 1000 €

    tarjeta_prueba.saldo += 1000
    print(tarjeta_prueba)
    # El saldo es 2000 €

    tarjeta_prueba.pagar(150)
    print(tarjeta_prueba)

    tarjeta_descuento=TarjetaDescuento("E454545454545", 10, 500)
    print(tarjeta_descuento)

    tarjeta_descuento.pagar(150)
    print(tarjeta_descuento)

    print(isinstance(tarjeta_prueba,Tarjeta))
    print(isinstance(tarjeta_prueba, tarjeta_descuento))
    print(isinstance(tarjeta_descuento,Tarjeta))
    print(isinstance(tarjeta_descuento, tarjeta_descuento))

lista_tarjetas=[]
lista_tarjetas.append(tarjeta_prueba)
lista_tarjetas.append(tarjeta_descuento)

for t in lista_tarjetas:
    t.pagar(150)
    if isinstance((t,TarjetaDescuento):
        print((f"Tiene de descuento {t._des}"))
    print(t)
