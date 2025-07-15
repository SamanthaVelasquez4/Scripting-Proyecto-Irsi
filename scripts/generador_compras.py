from faker import Faker
import random
from datetime import datetime
import csv
import subprocess

faker = Faker()  # Crear instancia de Faker para generar datos falsos

# Función para generar una compra falsa con datos realistas
def generar_compra():
    precio_unitario = random.randint(1000, 15000)          # Precio unitario aleatorio entre 1000 y 15000
    cantidad = random.randint(1, 10)                       # Cantidad aleatoria de productos (1 a 10)
    monto = precio_unitario * cantidad                     # Calcular monto total

    return {
        'id_transaccion': random.randint(1, 999999),       # ID aleatorio para la transacción
        'fecha_emision': datetime.now().strftime("%d-%m-%Y"),  
        'nombre': faker.name(),                             
        'ciudad': faker.city(),                             
        'direccion': faker.address().replace(',', ' -').replace('\n', ' '),  # Dirección sin comas ni saltos de línea
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

# Función para guardar la lista de compras en un archivo CSV
def guardar_compras_csv(compras, ruta_archivo):
    with open(ruta_archivo, 'w', newline='', encoding="utf-8") as csvfile:
        campos = list(compras[0].keys())                     # Obtener los nombres de las columnas
        writer = csv.DictWriter(csvfile, fieldnames=campos)  # Preparar escritor CSV con columnas
        writer.writeheader()                                 # Escribir fila de encabezados en CSV
        for compra in compras:
            writer.writerow(compra)                          # Escribir cada compra como fila en CSV


if __name__ == "__main__":
    cantidad_compras = 1  # Definir cuántas compras generar
    compras = [generar_compra() for _ in range(cantidad_compras)]  # Generar lista de compras

    # Definir ruta de la carpeta
    carpeta_compras = "./data/compras"
    
    # Verificar si la carpeta existe, si no, crearla
    if not os.path.exists(carpeta_compras):
        os.makedirs(carpeta_compras)
        print(f"Se creó la carpeta: {carpeta_compras}")

    # Nombre de archivo CSV con timestamp para evitar sobrescrituras
    archivo_compra = f"{carpeta_compras}/compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    guardar_compras_csv(compras, archivo_compra) # Ejecutar funcion para guardar compras en CSV

    print(f"**** Archivo CSV generado ****: {archivo_compra}")
    print("Generando factura automáticamente...")

    # # Ejecutar el script Bash que procesa el CSV y genera la factura PDF
    # subprocess.run(["bash", "./scripts/generador_facturas.sh"])