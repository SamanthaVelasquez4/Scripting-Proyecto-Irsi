# Variables de entorno
from dotenv import load_dotenv

# Librerías necesarias para enviar correos, manejar archivos y validaciones
import smtplib                # Para conectarse al servidor SMTP y enviar correos
import csv                   # Para leer y escribir archivos CSV
import os                    # Para rutas y operaciones con archivos
import glob
import re                    # Para validar correos con expresiones regulares
from email.mime.multipart import MIMEMultipart       # Para crear correos con partes (texto, adjunto, etc)
from email.mime.text import MIMEText                 # Para agregar el cuerpo del mensaje (texto plano)
from email.mime.base import MIMEBase                 # Para manejar archivos adjuntos
from email import encoders                           # Para codificar archivos adjuntos en base64
import subprocess

# Cargar variables de entorno
load_dotenv()

# --- Configuración de correo ---
SMTP_SERVER = "smtp.gmail.com"           # Servidor de correo SMTP de Gmail
SMTP_PORT = 587                          # Puerto estándar para STARTTLS
SMTP_USER = os.getenv("SMTP_USER")         # Usuario del correo remitente
SMTP_PASS = os.getenv("SMTP_PASS")         # Contraseña de aplicación (Generada de un correo gmail creado previamente)

print("Usuario:", SMTP_USER)
print("Contraseña:", SMTP_PASS)
# --- Ruta base del proyecto ---
# Esto permite encontrar la carpeta principal del proyecto desde donde esté este archivo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Rutas absolutas a archivos importantes ---
ARCHIVO_PENDIENTES = os.path.join(BASE_DIR, "data", "facturas_pdf", "pendientes_envio.csv")  # CSV con lista de facturas por enviar
ARCHIVO_LOG = os.path.join(BASE_DIR, "data", "facturas_pdf", "log_envios", "log_envios.csv") # CSV donde se guardan los resultados (éxito/fallo)




# --- Configuración y rutas (asume que ya están definidas las variables BASE_DIR, ARCHIVO_LOG, etc.) ---

log_diario_path = os.path.join(BASE_DIR, "data", "logs", "log_diario.log")

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
        return True 

    except Exception as e:
        error(f"Fallo al enviar a {correo_destino}: {e}")  # Se muestra el error si algo falla
        return False

# --- Procesar todos los correos pendientes ---
def procesar_envios():
    pendientes = leer_pendientes(ARCHIVO_PENDIENTES)  # Leemos la lista de pendientes
    # Crear carpeta log_envios si no existe
    os.makedirs(os.path.dirname(ARCHIVO_LOG), exist_ok=True)
    
    with open(ARCHIVO_LOG, 'a', newline='', encoding="utf-8") as f_log:
        log = csv.writer(f_log)
        for fila in pendientes:
            pdf, correo = fila[0].strip(), fila[1].strip()  # Limpiamos espacios extra
            estado = "exitoso" if enviar_factura(pdf, correo) else "fallido"  # Intentamos enviar
            registrar_log(pdf, correo, estado, log)  # Guardamos el resultado en el log
            print(f"El estado actual es: {estado}")


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



def enviar_reporte_admin(resumen_txt):
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
    # Contar líneas del log usando awk
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