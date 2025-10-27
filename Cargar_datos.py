import csv

aspirantes = []

class cargar_datos():
    def cargar(self):
        with open(r"C:\Users\LENOVO\Documents\GitClonacion\Proyecto-POO--CupoDrive-\BaseDatos.csv",newline="",encoding='utf-8') as data:
            lector = csv.reader(data,delimiter=";")
            next(lector)
            for fila in lector:
                aspirantes.append(fila)
        return aspirantes