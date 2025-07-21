"""
generador_compras.py

Script para generar datos falsos y realistas de compras en formato CSV.
Utiliza la librería Faker para simular datos de clientes, productos y pagos.

Requiere: Python 3.8+, faker

Funciones principales:
- generar_compra(): crea una compra ficticia con datos completos.
- guardar_compras_csv(): guarda una lista de compras en un archivo CSV.
- Genera un archivo CSV único con múltiples compras simuladas en ./data/compras/.

"""

from faker import Faker
import random
from datetime import datetime
import csv
import os

# Crear instancia Faker para generación de datos falsos
faker = Faker()

def generar_compra():
    """
    Genera una compra ficticia con datos realistas, incluyendo información
    del cliente, detalles del producto y datos de pago.
    
    """
    precio_unitario = random.randint(1000, 15000)          # Precio unitario entre 1000 y 15000
    cantidad = random.randint(1, 10)                       # Cantidad de productos (1 a 10)
    monto = precio_unitario * cantidad                     # Calcular monto total

    return {
        'id_transaccion': random.randint(1, 999999),
        'fecha_emision': datetime.now().strftime("%d-%m-%Y"),
        'nombre': faker.name(),
        'ciudad': faker.city(),
        'direccion': faker.address().replace(',', ' -').replace('\n', ' '),
        'correo': faker.email(),
        'telefono': faker.phone_number(),
        'ip': faker.ipv4(),
        'cantidad': cantidad,
        'monto_total': monto,
        'modalidad_pago': random.choice(['completo', 'fraccionado']),
        'estado_pago': random.choice(['exitoso', 'fallido']),
        'timestamp': datetime.now().strftime("%d %b %Y - %I:%M %p"),
        'observaciones': random.choice(['Cliente frecuente', 'Promoción aplicada'])
    }

def guardar_compras_csv(compras, ruta_archivo):
    """
    Guarda una lista de compras en un archivo CSV en la ruta especificada.

    Args:
        compras (list of dict): Lista de compras con datos de cada compra.
        ruta_archivo (str): Ruta del archivo CSV donde se guardarán las compras.
    """
    with open(ruta_archivo, 'w', newline='', encoding="utf-8") as csvfile:
        campos = list(compras[0].keys())                     # Obtener nombres de columnas del primer registro
        writer = csv.DictWriter(csvfile, fieldnames=campos)  # Crear escritor CSV con columnas definidas
        writer.writeheader()                                 # Escribir fila de encabezados
        for compra in compras:
            writer.writerow(compra)                          # Escribir cada compra como fila

if __name__ == "__main__":
    """
    Punto de entrada principal del script.
    Genera una cantidad aleatoria de compras y las guarda en un archivo CSV con timestamp.
    """
    cantidad_compras = random.randint(1, 10)                    # Número aleatorio de compras a generar
    compras = [generar_compra() for _ in range(cantidad_compras)]  # Generar lista de compras

    carpeta_compras = "./data/compras"

    # Crear carpeta si no existe
    if not os.path.exists(carpeta_compras):
        os.makedirs(carpeta_compras)
        print(f"Se creó la carpeta: {carpeta_compras}")

    # Nombre de archivo único con timestamp para evitar sobreescritura
    archivo_compra = f"{carpeta_compras}/compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    guardar_compras_csv(compras, archivo_compra)

    print(f"**** Archivo CSV generado ****: {archivo_compra}")
    print("Generando factura automáticamente...")
