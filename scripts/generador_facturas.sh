#!/bin/bash

# ══════════════════════════════════════════════════════
# Script: generador_facturas.sh
# Descripción: Genera facturas PDF a partir de archivos CSV de compras.
#              Utiliza plantillas LaTeX para crear facturas personalizadas.
# Uso:
#   bash generador_facturas.sh
# Requiere:
#   - pdflatex instalado
#   - plantilla LaTeX en ../templates/plantilla_factura_IRSI.tex
#   - archivos CSV en ../data/compras
# ══════════════════════════════════════════════════════

# OBTENER RUTA ABSOLUTA DEL SCRIPT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# CONFIGURACIÓN DE RUTAS BASADAS EN LA CARPETA DEL SCRIPT
TEMPLATE="$SCRIPT_DIR/../templates/plantilla_factura_IRSI.tex"   # Plantilla LaTeX
COMPRAS="$SCRIPT_DIR/../data/compras"                            # Carpeta con archivos CSV de compras
FACTURAS="$SCRIPT_DIR/../data/facturas_pdf"                      # Carpeta de salida para los PDFs
LOG_DIR="$SCRIPT_DIR/../data/logs"                               # Carpeta para logs individuales de cada factura
PENDIENTES="$FACTURAS/pendientes_envio.csv"                      # Archivo con lista de facturas pendientes por enviar

# Crear carpetas necesarias si no existen
mkdir -p "$FACTURAS" "$LOG_DIR"

# FUNCIÓN PARA ESCAPAR CARACTERES ESPECIALES EN LATEX
# Esto previene errores en la compilación de LaTeX por símbolos como $, %, _, etc.
escape_latex() {
    local str="$1"
    str="${str//\\/\\textbackslash}"
    str="${str//#/\\#}"
    str="${str//%/\\%}"
    str="${str//&/\\&}"
    str="${str//\$/\\\$}"
    str="${str//_/\\_}"
    echo "$str"
}

# PROCESAR CADA ARCHIVO DE COMPRAS
# Busca todos los archivos CSV tipo "compras_*.csv"

find "$COMPRAS" -type f -name "compras_*.csv" | while read -r CSV; do

    echo "Procesando: $CSV"

    # Omitimos encabezado con tail -n +2 y leemos campo por campo con read
    tail -n +2 "$CSV" | while IFS=',' read -r id fecha nombre ciudad direccion correo telefono ip cantidad monto pago estado timestamp obs; do
        PDF="$FACTURAS/factura_${id}.pdf"
        LOG_FACTURA="$LOG_DIR/factura_${id}.log"
        TEX_TEMP="$SCRIPT_DIR/factura_${id}.tex"

        # Omitir si ya existe una factura generada para ese ID
        [ -f "$PDF" ] && echo "Factura existente para ID $id. Omitida." && continue

        # Escapar todos los campos para LaTeX
        id=$(escape_latex "$id")
        fecha=$(escape_latex "$fecha")
        nombre=$(escape_latex "$nombre")
        ciudad=$(escape_latex "$ciudad")
        direccion=$(escape_latex "$direccion")
        correo=$(escape_latex "$correo")
        telefono=$(escape_latex "$telefono")
        ip=$(escape_latex "$ip")
        cantidad=$(escape_latex "$cantidad")
        monto=$(escape_latex "$monto")
        pago=$(escape_latex "$pago")
        estado=$(escape_latex "$estado")
        timestamp=$(escape_latex "$timestamp")
        obs=$(escape_latex "$obs")

        echo "" | tee -a "$LOG_FACTURA"
        echo "Generando factura ID $id para $nombre" | tee -a "$LOG_FACTURA"

        # Crear archivo .tex personalizado reemplazando los campos en la plantilla
        sed -e "s/{id_transaccion}/$id/g" \
            -e "s/{fecha_emision}/$fecha/g" \
            -e "s/{nombre}/$nombre/g" \
            -e "s/{correo}/$correo/g" \
            -e "s/{telefono}/$telefono/g" \
            -e "s/{direccion}/$direccion/g" \
            -e "s/{ciudad}/$ciudad/g" \
            -e "s/{cantidad}/$cantidad/g" \
            -e "s/{monto}/$monto/g" \
            -e "s/{pago}/$pago/g" \
            -e "s/{estado_pago}/$estado/g" \
            -e "s/{ip}/$ip/g" \
            -e "s/{timestamp}/$timestamp/g" \
            -e "s/{observaciones}/$obs/g" \
            "$TEMPLATE" > "$TEX_TEMP"

        # Compilar LaTeX a PDF
        pdflatex -interaction=nonstopmode -output-directory="$FACTURAS" "$TEX_TEMP" 2>&1

        # Validar éxito de la compilación
        if grep -q "^!" "$LOG_FACTURA"; then
            echo "ERROR: Falló la compilación para ID $id" | tee -a "$LOG_FACTURA"
            tail -n 5 "$LOG_FACTURA"
        elif [ -f "$PDF" ]; then
            echo "Factura generada: $PDF" | tee -a "$LOG_FACTURA"
            echo "factura_${id}.pdf,$correo" >> "$PENDIENTES"
        else
            echo "ADVERTENCIA: PDF no encontrado para ID $id" | tee -a "$LOG_FACTURA"
        fi

        # Limpiar archivos temporales de LaTeX
        rm -f "$TEX_TEMP" "$FACTURAS/factura_${id}".{aux,log,out}

    done
done
