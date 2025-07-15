import smtplib
import csv
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- Configuración de correo ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "wrrrsgrp@gmail.com"
SMTP_PASS = "pcyl yfbh dkza pqsp"

# BASE_DIR = carpeta raíz del proyecto (subimos desde /scripts)
# --- Ruta base absoluta del script ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- Rutas de relativas archivos (No usar para TaskScheduler)---
# ARCHIVO_PENDIENTES = "./data/facturas_pdf/pendientes_envio.csv"
# ARCHIVO_LOG = "./data/facturas_pdf/log_envios/log_envios.csv"

# Rutas absolutas
ARCHIVO_PENDIENTES = os.path.join(BASE_DIR, "data", "facturas_pdf", "pendientes_envio.csv")
ARCHIVO_LOG = os.path.join(BASE_DIR, "data", "facturas_pdf", "log_envios", "log_envios.csv")



# --- Utilidades de consola ---
def info(msg):
    print(f"🟢 [OK] {msg}")

def error(msg):
    print(f"🔴 [ERROR] {msg}")

# --- Validar correo con expresión regular ---
def correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

# --- Leer pendientes del archivo CSV ---
def leer_pendientes(path):
    with open(path, newline='', encoding="utf-8") as f:
        return [line for line in csv.reader(f) if len(line) >= 2]

# --- Registrar resultado en el log ---
def registrar_log(pdf, correo, estado, escritor):
    escritor.writerow([pdf, correo, estado])

# --- Enviar factura por correo con PDF adjunto ---
def enviar_factura(pdf, correo_destino):
    # ruta_pdf = os.path.join("./data/facturas_pdf", pdf)
    ruta_pdf = os.path.join(BASE_DIR, "data", "facturas_pdf", pdf)


    if not os.path.isfile(ruta_pdf):
        error(f"Archivo no encontrado: {pdf}")
        return False

    if not correo_valido(correo_destino):
        error(f"Correo inválido: {correo_destino}")
        return False

    try:
        mensaje = MIMEMultipart()
        mensaje['From'] = SMTP_USER
        mensaje['To'] = correo_destino
        mensaje['Subject'] = "Factura generada"
        mensaje.attach(MIMEText("Adjuntamos su factura generada. Gracias por su compra.", 'plain'))

        with open(ruta_pdf, "rb") as f:
            adjunto = MIMEBase('application', 'octet-stream')
            adjunto.set_payload(f.read())
            encoders.encode_base64(adjunto)
            adjunto.add_header('Content-Disposition', f'attachment; filename={pdf}')
            mensaje.attach(adjunto)

        servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASS)
        servidor.send_message(mensaje)
        servidor.quit()

        info(f"Correo enviado a {correo_destino}")
        return True

    except Exception as e:
        error(f"Fallo al enviar a {correo_destino}: {e}")
        return False

# --- Procesar todos los envíos ---
def procesar_envios():
    pendientes = leer_pendientes(ARCHIVO_PENDIENTES)
    with open(ARCHIVO_LOG, 'a', newline='', encoding="utf-8") as f_log:
        log = csv.writer(f_log)
        for fila in pendientes:
            pdf, correo = fila[0].strip(), fila[1].strip()
            estado = "exitoso" if enviar_factura(pdf, correo) else "fallido"
            registrar_log(pdf, correo, estado, log)

# --- Eliminar líneas exitosas del archivo pendientes ---
def limpiar_pendientes():
    try:
        with open(ARCHIVO_LOG, newline='', encoding="utf-8") as f:
            enviados = {line[0] for line in csv.reader(f) if len(line) == 3 and line[2] == "exitoso"}

        with open(ARCHIVO_PENDIENTES, newline='', encoding="utf-8") as f:
            actuales = [line for line in csv.reader(f)]

        nuevos = [line for line in actuales if line and line[0] not in enviados]

        with open(ARCHIVO_PENDIENTES, 'w', newline='', encoding="utf-8") as f:
            csv.writer(f).writerows(nuevos)

        info("Líneas exitosas eliminadas del archivo pendientes_envio.csv")
    except Exception as e:
        error(f"Error al limpiar pendientes: {e}")

# --- Ejecutar programa principal ---
if __name__ == "__main__":
    procesar_envios()
    limpiar_pendientes()
