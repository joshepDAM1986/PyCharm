from Empleado import Empleado


class Vendedor(Empleado):
    def __init__(self, nombre, dni, sueldo_base, años_en_empresa, ventas_totales, comision_por_venta):
        super().__init__(nombre, dni, sueldo_base, años_en_empresa)
        self.ventas_totales = ventas_totales
        self.comision_por_venta = comision_por_venta

    def sueldo_neto(self):
        sueldo_base = super().sueldo_neto()
        comision_total = self.ventas_totales * self.comision_por_venta
        sueldo_final = sueldo_base + comision_total
        return sueldo_final

    def vender(self):
        print(f"{self.nombre} ha realizado una venta.")

    def __str__(self):
        sueldo_final = self.sueldo_neto()
        return f"{super().__str__()}\nVentas Totales: {self.ventas_totales}\nComisión por Venta: ${self.comision_por_venta}\nSueldo Final: ${sueldo_final}"
