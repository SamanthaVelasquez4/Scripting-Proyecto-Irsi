"""
enviador.py

Script para enviar facturas PDF por correo, gestionar pendientes y logs de envío,
y generar reportes diarios con estadísticas de ventas.

Requiere: Python 3.8+, dotenv, smtplib, csv, glob, re, email, subprocess

Este script:
- Carga credenciales desde variables de entorno (.env)
- Lee archivos CSV con facturas pendientes para enviar
- Valida correos y archivos PDF adjuntos
- Envía correos con facturas en PDF
- Registra resultados en un archivo log CSV
- Limpia pendientes enviados con éxito
- Genera y almacena un resumen diario con estadísticas de ventas
- Envía reporte diario al administrador vía correo

"""

from dotenv import load_dotenv
import smtplib                                      # Para conectarse al servidor SMTP y enviar correos
import csv                                          # Para leer y escribir archivos CSV
import os                                           # Para rutas y operaciones con archivos
import glob
import re                                           # Para validar correos con expresiones regulares
from email.mime.multipart import MIMEMultipart      # Para crear correos con partes (texto, adjunto, etc)
from email.mime.text import MIMEText                # Para agregar el cuerpo del mensaje (texto plano)
from email.mime.base import MIMEBase                # Para manejar archivos adjuntos
from email import encoders                          # Para codificar archivos adjuntos en base64
import subprocess

# Cargar variables de entorno desde archivo .env que debe estar en la raíz del proyecto
load_dotenv()

# --- Configuración de correo ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")     # Usuario del correo remitente
SMTP_PASS = os.getenv("SMTP_PASS")     # Contraseña de aplicación generada desde Gmail

# print("Usuario:", SMTP_USER)
# print("Contraseña:", SMTP_PASS)

# --- Rutas base del proyecto ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rutas importantes:
# - ARCHIVO_PENDIENTES: archivo CSV con facturas pendientes por enviar (formato: pdf, correo)
# - ARCHIVO_LOG: archivo CSV donde se registra el resultado de cada envío (formato: pdf, correo, estado)
# - log_diario_path: archivo de texto con resumen diario de ventas y envíos
ARCHIVO_PENDIENTES = os.path.join(BASE_DIR, "data", "facturas_pdf", "pendientes_envio.csv")
ARCHIVO_LOG = os.path.join(BASE_DIR, "data", "facturas_pdf", "log_envios", "log_envios.csv")
log_diario_path = os.path.join(BASE_DIR, "data", "logs", "log_diario.log")

# --- Funciones utilitarias ---

def info(msg):
    """Muestra un mensaje de éxito en consola con formato verde."""
    print(f"[OK] {msg}")  

def error(msg):
    """Muestra un mensaje de error en consola con formato rojo."""
    print(f"[ERROR] {msg}")  


def correo_valido(correo):
    """
    Verifica si el correo tiene un formato válido usando una expresión regular.

    Args:
        correo (str): Dirección de correo electrónico a validar.

    Returns:
        bool: True si el correo es válido, False en caso contrario.
    """
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

def leer_pendientes(path):
    """
    Lee el archivo CSV de facturas pendientes y devuelve solo las filas con al menos dos columnas.

    Args:
        path (str): Ruta al archivo CSV de pendientes.

    Returns:
        list[list]: Lista de filas, cada una con datos mínimos [pdf, correo].
    """
    with open(path, newline='', encoding="utf-8") as f:
        return [line for line in csv.reader(f) if len(line) >= 2]

def registrar_log(pdf, correo, estado, escritor):
    """
    Registra en el archivo log el estado de envío de una factura.

    Args:
        pdf (str): Nombre del archivo PDF enviado.
        correo (str): Correo electrónico de destino.
        estado (str): Estado del envío ('exitoso' o 'fallido').
        escritor (csv.writer): Objeto escritor CSV abierto para agregar la línea.
    """
    escritor.writerow([pdf, correo, estado])

def enviar_factura(pdf, correo_destino):
    """
    Envía una factura PDF adjunta por correo electrónico.

    Args:
        pdf (str): Nombre del archivo PDF a enviar.
        correo_destino (str): Dirección de correo destino.

    Returns:
        bool: True si el correo se envió correctamente, False si hubo fallo.
    """
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

def procesar_envios():
    """
    Procesa todas las facturas pendientes para enviar los correos con sus PDFs.
    Registra el resultado (éxito/fallo) en el archivo log CSV.
    """
    pendientes = leer_pendientes(ARCHIVO_PENDIENTES)
    os.makedirs(os.path.dirname(ARCHIVO_LOG), exist_ok=True)

    with open(ARCHIVO_LOG, 'a', newline='', encoding="utf-8") as f_log:
        log = csv.writer(f_log)
        for fila in pendientes:
            pdf, correo = fila[0].strip(), fila[1].strip()
            estado = "exitoso" if enviar_factura(pdf, correo) else "fallido"
            registrar_log(pdf, correo, estado, log)
            print(f"El estado actual es: {estado}")

def limpiar_pendientes():
    """
    Limpia el archivo de pendientes eliminando las facturas que ya fueron enviadas exitosamente.
    """
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

def enviar_reporte_admin(resumen_txt):
    """
    Envía un reporte diario por correo al administrador con resumen de envíos.

    Args:
        resumen_txt (str): Texto con el resumen diario a enviar.
    """
    try:
        mensaje = MIMEMultipart()
        mensaje['From'] = SMTP_USER
        mensaje['To'] = SMTP_USER
        mensaje['Subject'] = "📋 Reporte Diario de Envíos"
        cuerpo = MIMEText(resumen_txt, 'plain')
        mensaje.attach(cuerpo)

        servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASS)
        servidor.send_message(mensaje)
        servidor.quit()

        info("Reporte diario enviado al administrador.")
    except Exception as e:
        error(f"Error al enviar el reporte al administrador: {e}")

def contar_registros(log_path):
    """
    Cuenta cuántas líneas válidas (con 3 columnas) hay en el archivo log.

    Args:
        log_path (str): Ruta del archivo log CSV.

    Returns:
        int: Número total de registros válidos en el log.
    """
    comando = f'awk -F"," \'NF==3 {{count++}} END {{print count}}\' "{log_path}"'
    resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
    if resultado.returncode == 0:
        try:
            return int(resultado.stdout.strip())
        except ValueError:
            error("Error al convertir la salida de awk a entero.")
            return 0
    else:
        error(f"No se pudo contar líneas con awk: {resultado.stderr}")
        return 0

def almacenar_log_diario(enviar=False):
    """
    Genera un resumen diario con estadísticas de ventas y envíos,
    lo guarda en archivo log y opcionalmente lo envía por correo.

    Args:
        enviar (bool): Si True, envía el resumen por correo al administrador.
    """
    total_correos = contar_registros(ARCHIVO_LOG)

    total_vendido = 0
    pedidos_completos = 0
    pedidos_exitosos = 0
    pedidos_fallidos = 0

    compras_path = os.path.join(BASE_DIR, "data", "compras", "compras_*.csv")
    for archivo in glob.glob(compras_path):
        with open(archivo, encoding='utf-8') as f:
            lector = csv.DictReader(f)
            for row in lector:
                if row["estado_pago"] == "exitoso":
                    total_vendido += float(row['monto_total'])
                    pedidos_exitosos += 1
                    if row['modalidad_pago'].strip().lower() == "completo":
                        pedidos_completos += 1
                elif row["estado_pago"] == "fallido":
                    pedidos_fallidos += 1

    resumen = (
        f"Total de correos procesados: {total_correos}\n"
        f"Pedidos exitosos: {pedidos_exitosos}\n"
        f"Pedidos fallidos: {pedidos_fallidos}\n"
        f"Total vendido: ₡{total_vendido:.2f}\n"
        f"Pedidos con pago completo: {pedidos_completos}\n"
        "---------------------------------------------\n"
    )

    os.makedirs(os.path.dirname(log_diario_path), exist_ok=True)
    with open(log_diario_path, 'a', encoding='utf-8') as f:
        f.write(resumen)

    if enviar:
        enviar_reporte_admin(resumen)

if __name__ == "__main__":
    procesar_envios()
    limpiar_pendientes()
    almacenar_log_diario()
