from Empleado import Empleado
from Vendedor import Vendedor


class Empresa:
    def __init__(self, nombre):
        self.nombre = nombre
        self.lista_empleados = []

    def contratar_trabajador(self, empleado):
        self.lista_empleados.append(empleado)

    def imprimir_resumen(self):
        for empleado in self.lista_empleados:
            print(empleado)
            if isinstance(empleado, Vendedor):
                empleado.vender()
            print("\n")

empresa = Empresa("Mi Empresa")

empleado1 = Empleado("Juan", "123456789", 3000, 5)
vendedor1 = Vendedor("Ana", "987654321", 2500, 3, 100000, 0.05)

empresa.contratar_trabajador(empleado1)
empresa.contratar_trabajador(vendedor1)

empresa.imprimir_resumen()