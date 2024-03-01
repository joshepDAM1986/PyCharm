# EJERCICIO 6
# Crear la aplicación para la gestión de empleados de una empresa que está compuesta por varias clases:
# - La clase Empleado tiene cuatro atributos: nombre, dni como cadena de texto, sueldo_base y años en la
# empresa. Implementar el método __init__, y __eq__ (mismo dni mismo empleado), además del método
# sueldo_neto que devuelve un float con el sueldo deduciéndole un 15% de impuestos. Debe implementarse
# también un método __str__ que debe mostrar todos los atributos y el sueldoFinal debe aparecer dentro del
# string que devuelve el __str__.
# - La clase Vendedor que hereda de Empleado y tiene como atributos propios las ventas totales realizadas
# por el vendedor y la comisión que se lleva por venta realizada. Hay que redefinir el método __str__ con
# los nuevos datos y también sueldo_neto añadiendo la comisión total por ventas realizadas al cálculo que
# realiza la clase Empleado.
# - Por último, la clase Vendedor tiene un método llamado vender que lanzar un mensaje por pantalla
# informativo.
# - La clase Empresa que tiene 2 atributos que son el nombre de la empresa y una lista que está
# inicialmente vacía. El nombre de la empresa se le pasa al constructor.
# - La clase Empresa tendrá un método para añadir objetos de las clases anteriores a la lista, llamado
# contratar_trabajador.
# - Por último, la clase Empresa tendrá un método llamado imprimir_resumen que recorre la lista
# completamente y para cada objeto (que puede ser Empleado o Vendedor) hace un print de lo que
# devuelve el método __str__ correspondiente, donde además en caso de ser un objeto de la clase
# Vendedor ejecutar también el método vender.

class Empleado:
    def __init__(self, nombre, dni, sueldo_base, años_en_empresa):
        self.nombre = nombre
        self.dni = dni
        self.sueldo_base = sueldo_base
        self.años_en_empresa = años_en_empresa

    def __eq__(self, other):
        return self.dni == other.dni

    def sueldo_neto(self):
        impuestos = 0.15
        sueldo_final = self.sueldo_base * (1 - impuestos)
        return sueldo_final

    def __str__(self):
        sueldo_final = self.sueldo_neto()
        return f"Nombre: {self.nombre}\nDNI: {self.dni}\nSueldo Base: ${self.sueldo_base}\nAños en la empresa: {self.años_en_empresa}\nSueldo Final: ${sueldo_final}"