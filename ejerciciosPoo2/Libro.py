# EJERCICIO 2 Crea una clase llamada Libro que guarde la información acerca de un libro de una biblioteca.
# La clase debe guardar el título del libro, ISBN, autor, número de ejemplares totales del libro y número
# de ejemplares prestados. La clase contendrá los siguientes métodos:
# - Constructor__init__.
# - Método __str__.
# - Método __eq__ donde dos libros son iguales si tienen el mismo ISBN.
# - Método llamado préstamo que incremente el atributo correspondiente cada vez que se realice un préstamo del libro.
# No se podrán prestar libros de los que no queden ejemplares disponibles para prestar.
# - Método devolución que produce la devolución de un libro. Si no se ha prestado ningún libro no se puede devolver.

class Libro:
    def __init__(self,titulo,ISBN,autor,ejemplares,prestamos=0):
        self._titulo=titulo
        self._ISBN=ISBN
        self._autor=autor
        self._ejemplares=ejemplares
        self._prestamos=prestamos

    def hacerPrestamo(self):
        if self._ejemplares>self._prestamos:
            self._prestamos+=1
            print("Préstamo realizado")
        else:
            print("No hay ejemplares para prestar")
            #raise RuntimeError("No hay ejemplares para prestar")
    def hacerDevolucion(self):
        if self._prestamos>0:
            self._prestamos-=1
            print("Devolvución realizada")
        else:
            print("No se puede devolver ejemplares no prestados")

    def __str__(self):
        return f"Título: {self._titulo}, ISBN: {self._ISBN}, autor: {self._autor}, ejemplares totales: {self._ejemplares}, préstamos: {self._prestamos}"

    def __eq__(self,otro):
        return self._ISBN==otro._ISBN


if __name__=="__main__":

    libro1=Libro("titulo libro1","987654321", "autor libro1",5,0)
    print(libro1)
    libro2=Libro("titulo libro2","123456789", "autor libro2",5,5)
    print(libro2)

    if libro1==libro2:
        print("Iguales")
    else:
        print("No iguales")

    libro1.hacerPrestamo()
    print(libro1)
    libro2.hacerPrestamo()
    print(libro2)

    libro1.hacerDevolucion()
    print(libro1)
    libro2.hacerDevolucion()
    print(libro2)


