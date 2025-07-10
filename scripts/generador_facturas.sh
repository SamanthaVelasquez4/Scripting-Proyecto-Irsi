#!/bin/bash  
# Shell: Bash  # Indica que se usará Bash para ejecutar el script


# Rutas de archivos individuales
TEMPLATE="./templates/plantilla_factura_IRSI.tex"         # Plantilla LaTeX con campos a reemplazar
LOG_DIARIO="./data/logs/log_diario.log"                   # Archivo de log general por ejecución
PENDIENTES="./data/facturas_pdf/pendientes_envio.csv"     # CSV con facturas pendientes por enviar

# Rutas de carpetas utilizadas por el script
COMPRAS="./data/compras"                                  # Carpeta con archivos CSV de compras
FACTURAS="./data/facturas_pdf"                            # Carpeta donde se guardarán los PDFs
LOG_DIR="./data/logs"                                     # Carpeta que contiene todos los logs


# Crear carpetas si no existen
mkdir -p "$FACTURAS"
mkdir -p "$LOG_DIR"

# Limpiar archivos de log anteriores
# echo "" > "$LOG_DIARIO"
# echo "" > "$PENDIENTES"

# Función que escapa caracteres especiales para que no den error en LaTeX
escape_latex() {
    local str="$1"
    str="${str//\\/\\textbackslash}"   # escapamos \ 
    str="${str//#/\\#}"
    str="${str//%/\\%}"
    str="${str//&/\\&}"
    str="${str//\$/\\\$}"
    str="${str//_/\\_}"
    str="${str//@/\\@}"
    # str="${str//^/\\^{}}"
    # str="${str//~/\\~{}}"
    echo "$str"
}

# Detectar el archivo CSV más reciente en la carpeta de compras
CSV=$(find "$COMPRAS" -type f -name "compras_*.csv" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-)

echo "Archivo CSV detectado: $CSV"

# Validar si se encontró un archivo CSV válido
if [ -z "$CSV" ] || [ ! -f "$CSV" ]; then
  echo "❌ No se encontró ningún archivo CSV válido en $COMPRAS"
  exit 1
fi

procesar_factura(){

    # Leer línea por línea el CSV (omitir encabezado con tail)
    tail -n +2 "$CSV" | while IFS=',' read -r id_transaccion fecha_emision nombre ciudad direccion correo telefono ip cantidad monto_total modalidad_pago estado_pago timestamp observaciones
    do
        # Escapar caracteres especiales en cada campo del CSV
        id_transaccion_esc=$(escape_latex "$id_transaccion")
        fecha_emision_esc=$(escape_latex "$fecha_emision")
        nombre_esc=$(escape_latex "$nombre")
        ciudad_esc=$(escape_latex "$ciudad")
        direccion_esc=$(escape_latex "$direccion")
        correo_esc=$(escape_latex "$correo")
        telefono_esc=$(escape_latex "$telefono")
        ip_esc=$(escape_latex "$ip")
        cantidad_esc=$(escape_latex "$cantidad")
        monto_total_esc=$(escape_latex "$monto_total")
        modalidad_pago_esc=$(escape_latex "$modalidad_pago")
        estado_pago_esc=$(escape_latex "$estado_pago")
        timestamp_esc=$(escape_latex "$timestamp")
        observaciones_esc=$(escape_latex "$observaciones")


        echo "Procesando factura ID $id_transaccion para $nombre" | tee -a "$LOG_DIARIO"

        # Nombre temporal del archivo .tex generado
        TEX_TEMP="factura_${id_transaccion}.tex"

        # Reemplazar los marcadores del template con los valores escapados
        sed -e "s/{id_transaccion}/$id_transaccion_esc/g" \
            -e "s/{fecha_emision}/$fecha_emision_esc/g" \
            -e "s/{nombre}/$nombre_esc/g" \
            -e "s/{correo}/$correo_esc/g" \
            -e "s/{telefono}/$telefono_esc/g" \
            -e "s/{direccion}/$direccion_esc/g" \
            -e "s/{ciudad}/$ciudad_esc/g" \
            -e "s/{cantidad}/$cantidad_esc/g" \
            -e "s/{monto}/$monto_total_esc/g" \
            -e "s/{pago}/$modalidad_pago_esc/g" \
            -e "s/{estado_pago}/$estado_pago_esc/g" \
            -e "s/{ip}/$ip_esc/g" \
            -e "s/{timestamp}/$timestamp_esc/g" \
            -e "s/{observaciones}/$observaciones_esc/g" \
            "$TEMPLATE" > "$TEX_TEMP"

        # Compilar el archivo .tex a PDF usando pdflatex
        pdflatex -interaction=nonstopmode -output-directory="$FACTURAS" "$TEX_TEMP" > "$LOG_DIR/factura_${id_transaccion}.log" 2>&1

        # Verificar si hubo errores en el log de compilación
        if grep -q "^!" "$LOG_DIR/factura_${id_transaccion}.log"; then
            echo " ***❌ Error*** al compilar factura ID $id_transaccion" | tee -a "$LOG_DIARIO"
            echo "---- Contenido del log ----"
            tail -n 20 "$LOG_DIR/factura_${id_transaccion}.log"
        else
            # Verificar si el PDF fue generado correctamente
            if [ -f "$FACTURAS/factura_${id_transaccion}.pdf" ]; then
                echo "✅ [APROBADO] Factura ID $id_transaccion generada correctamente" | tee -a "$LOG_DIARIO"
                echo "factura_${id_transaccion}.pdf,$correo" >> "$PENDIENTES"
            else
                echo "***! Error*** PDF temporal no encontrado para factura ID $id_transaccion" | tee -a "$LOG_DIARIO"
            fi
        fi

        # Limpiar archivos temporales generados por LaTeX
        rm -f "$FACTURAS/factura_${id_transaccion}.aux" \
            "$FACTURAS/factura_${id_transaccion}.out" \
            "$FACTURAS/factura_${id_transaccion}.log"

    done


}

# Ejecutar función
procesar_factura