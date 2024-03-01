class DocumetoGeneral:
    def __init__(self,titulo,paginas):
        self._titulo=titulo
        self._paginas=paginas

    def __str__(self):
        return f"Titulo: {self._titulo}, páginas: {self._paginas}"

    def __eq__(self, other):
        return self._titulo==other._titulo

    def leerVozAlta(self):
        return "Se leyó el documento"

    def recordarPagina(self):
        return "Se recordó la página del documento"

class DocumentoFisico(DocumetoGeneral):
    def __init__(self,titulo,paginas,encuadernacion,bolsillo):
        super().__init__(titulo,paginas)
        self._encuadernacion=encuadernacion
        self._bolsillo=bolsillo

    def __str__(self):
        return f"{super().__str__()}, encuadernación: {self._encuadernacion}, bolsillo: {self._bolsillo}"

    def leerVozAlta(self):
        return super().leerVozAlta()

    def recordarPagina(self):
        return super().recordarPagina()

    def digitalizarPDF(self):
        return "se digitalizó el documento"

class DocumentoDigital(DocumetoGeneral):
    def __init__(self,titulo,paginas,formato,bytes):
        super().__init__(titulo,paginas)
        self._formato=formato
        self._bytes=bytes

    def __str__(self):
        return f"{super().__str__()}, formato: {self._formato}, bytes: {self._bytes}"

    def leerVozAlta(self):
        return super().leerVozAlta()

    def recordarPagina(self):
        return super().recordarPagina()

    def imprimirPapel(self):
        return "Se imprimió el documento"

if __name__ == "__main__":

    documentoFisico=DocumentoFisico("Crónicas de Idum",303,"Dura",True)
    documentoDigital=DocumentoDigital("Crónicas de Narnia", 333, "PDF", 3.333)

    print("===================FISICO====================")

    print(documentoFisico.leerVozAlta()+ " físico")
    print(documentoFisico.recordarPagina() + " físico")
    print(documentoFisico.digitalizarPDF())

    print("===================DIGITAL====================")

    print(documentoDigital.leerVozAlta()+ " digital")
    print(documentoDigital.recordarPagina()+ " digital")
    print(documentoDigital.imprimirPapel())

    if documentoFisico==documentoDigital:
        print("Iguales")
    else:
        print("No iguales")

