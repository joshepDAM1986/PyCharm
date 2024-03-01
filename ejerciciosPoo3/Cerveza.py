class Cerveza:
    contador=1
    def __init__(self,nombre, tipo,artesanal,precio,existencias):
        self.codigo=f"CERV-{Cerveza.contador}"
        Cerveza.contador += 1
        self._nombre=nombre
        self._tipo=tipo
        self._artesanal=artesanal
        self._precio=precio
        self._existencias=existencias
        
    def __str__(self):
        return f"{self.codigo}, nombre: {self._nombre}, tipo: {self._tipo}, artesanal: {self._artesanal}, precio: {self._precio}, existencias: {self._existencias}"

    def servir(self,unidades):
        if unidades<=self._existencias:
            self._existencias-=unidades
            print("hay suficientes")
        else:
            print("no hay suficientes")
            print(f"Se han servido {self._existencias}")
            self._existencias=0

if __name__ == '__main__':
    c1=Cerveza("Alhambra 1925", "Rubia",False,3,450)
    print(c1)
    c2=Cerveza("Victoria", "Rubia",True,2,100)
    print(c2)

Cerveza.servir(10)