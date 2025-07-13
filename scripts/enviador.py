# Librerías necesarias para enviar correos, manejar archivos y validaciones
import smtplib                # Para conectarse al servidor SMTP y enviar correos
import csv                   # Para leer y escribir archivos CSV
import os                    # Para rutas y operaciones con archivos
import re                    # Para validar correos con expresiones regulares
from email.mime.multipart import MIMEMultipart       # Para crear correos con partes (texto, adjunto, etc)
from email.mime.text import MIMEText                 # Para agregar el cuerpo del mensaje (texto plano)
from email.mime.base import MIMEBase                 # Para manejar archivos adjuntos
from email import encoders                           # Para codificar archivos adjuntos en base64

# --- Configuración de correo ---
SMTP_SERVER = "smtp.gmail.com"           # Servidor de correo SMTP de Gmail
SMTP_PORT = 587                          # Puerto estándar para STARTTLS
SMTP_USER = "wrrrsgrp@gmail.com"         # Usuario del correo remitente
SMTP_PASS = "pcyl yfbh dkza pqsp"        # Contraseña de aplicación (Generada de un correo gmail creado previamente)

# --- Ruta base del proyecto ---
# Esto permite encontrar la carpeta principal del proyecto desde donde esté este archivo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Rutas absolutas a archivos importantes ---
ARCHIVO_PENDIENTES = os.path.join(BASE_DIR, "data", "facturas_pdf", "pendientes_envio.csv")  # CSV con lista de facturas por enviar
ARCHIVO_LOG = os.path.join(BASE_DIR, "data", "facturas_pdf", "log_envios", "log_envios.csv") # CSV donde se guardan los resultados (éxito/fallo)

# --- Funciones para mostrar mensajes bonitos en consola ---
def info(msg):
    print(f"[OK] {msg}")  

def error(msg):
    print(f"[ERROR] {msg}")  

# --- Verificar si un correo tiene un formato válido ---
def correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'     # Regex básico para validar correos
    return re.match(patron, correo) is not None

# --- Leer pendientes del archivo CSV ---
def leer_pendientes(path):
    with open(path, newline='', encoding="utf-8") as f:    # Abrimos el archivo
        return [line for line in csv.reader(f) if len(line) >= 2]  # Devolvemos solo líneas con al menos 2 columnas (PDF, correo)

# --- Guardar en el log si se envió o falló ---
def registrar_log(pdf, correo, estado, escritor):
    escritor.writerow([pdf, correo, estado])  # Escribe una línea nueva en el log

# --- Función que envía la factura por correo con el PDF adjunto ---
def enviar_factura(pdf, correo_destino):
    # Construir la ruta al archivo PDF
    ruta_pdf = os.path.join(BASE_DIR, "data", "facturas_pdf", pdf)

    # Verificar si el archivo existe
    if not os.path.isfile(ruta_pdf):
        error(f"Archivo no encontrado: {pdf}")
        return False

    # Verificar si el correo es válido
    if not correo_valido(correo_destino):
        error(f"Correo inválido: {correo_destino}")
        return False

    try:
        # Crear el mensaje de correo
        mensaje = MIMEMultipart()
        mensaje['From'] = SMTP_USER
        mensaje['To'] = correo_destino
        mensaje['Subject'] = "Factura generada"  # Asunto del correo

        # Cuerpo del mensaje
        mensaje.attach(MIMEText("Adjuntamos su factura generada. Gracias por su compra.", 'plain'))

        # Adjuntar el archivo PDF
        with open(ruta_pdf, "rb") as f:
            adjunto = MIMEBase('application', 'octet-stream')  # Tipo genérico de archivo
            adjunto.set_payload(f.read())                     # Leemos el contenido binario
            encoders.encode_base64(adjunto)                   # Lo codificamos en base64
            adjunto.add_header('Content-Disposition', f'attachment; filename={pdf}')  # Nombre del archivo adjunto
            mensaje.attach(adjunto)                           # Se agrega al mensaje

        # Enviar el correo usando SMTP con STARTTLS (encriptado)
        servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        servidor.starttls()                                  # Se establece conexión segura
        servidor.login(SMTP_USER, SMTP_PASS)                 # Se inicia sesión
        servidor.send_message(mensaje)                       # Se envía el correo
        servidor.quit()                                      # Se cierra la conexión

        info(f"Correo enviado a {correo_destino}")
        return True  # Todo salió bien

    except Exception as e:
        error(f"Fallo al enviar a {correo_destino}: {e}")  # Se muestra el error si algo falla
        return False

# --- Procesar todos los correos pendientes ---
def procesar_envios():
    pendientes = leer_pendientes(ARCHIVO_PENDIENTES)  # Leemos la lista de pendientes
    with open(ARCHIVO_LOG, 'a', newline='', encoding="utf-8") as f_log:
        log = csv.writer(f_log)
        for fila in pendientes:
            pdf, correo = fila[0].strip(), fila[1].strip()  # Limpiamos espacios extra
            estado = "exitoso" if enviar_factura(pdf, correo) else "fallido"  # Intentamos enviar
            registrar_log(pdf, correo, estado, log)  # Guardamos el resultado en el log

# --- Limpiar la lista de pendientes eliminando los que se enviaron bien ---
def limpiar_pendientes():
    try:
        # Leer los que se enviaron exitosamente desde el log
        with open(ARCHIVO_LOG, newline='', encoding="utf-8") as f:
            enviados = {line[0] for line in csv.reader(f) if len(line) == 3 and line[2] == "exitoso"}

        # Leer los pendientes actuales
        with open(ARCHIVO_PENDIENTES, newline='', encoding="utf-8") as f:
            actuales = [line for line in csv.reader(f)]

        # Conservar solo los que no se han enviado aún
        nuevos = [line for line in actuales if line and line[0] not in enviados]

        # Escribir nuevamente el archivo pendientes, con solo los que faltan
        with open(ARCHIVO_PENDIENTES, 'w', newline='', encoding="utf-8") as f:
            csv.writer(f).writerows(nuevos)

        info("Líneas exitosas eliminadas del archivo pendientes_envio.csv")

    except Exception as e:
        error(f"Error al limpiar pendientes: {e}") 

# --- Programa principal que se ejecuta si corres este archivo directamente ---
if __name__ == "__main__":
    procesar_envios()     
    limpiar_pendientes()  
