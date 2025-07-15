#!/bin/bash

# ──────────────────────────────────────────────────────
# Generador de facturas PDF desde archivos CSV de compras
# ──────────────────────────────────────────────────────

# OBTENER RUTA ABSOLUTA DEL SCRIPT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# CONFIGURACIÓN DE RUTAS BASADAS EN LA CARPETA DEL SCRIPT
TEMPLATE="$SCRIPT_DIR/../templates/plantilla_factura_IRSI.tex"
COMPRAS="$SCRIPT_DIR/../data/compras"
FACTURAS="$SCRIPT_DIR/../data/facturas_pdf"
LOG_DIR="$SCRIPT_DIR/../data/logs"
LOG_DIARIO="$LOG_DIR/log_diario.log"
PENDIENTES="$FACTURAS/pendientes_envio.csv"

# Crear carpetas necesarias
mkdir -p "$FACTURAS" "$LOG_DIR"

# FUNCIÓN PARA ESCAPAR CARACTERES ESPECIALES EN LATEX
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

# ENCONTRAR Y PROCESAR SOLO EL ÚLTIMO ARCHIVO DE COMPRAS
latest_csv=$(find "$COMPRAS" -type f -name "compras_*.csv" | sort -r | head -n 1)

if [ -n "$latest_csv" ]; then
    echo "Procesando archivo más reciente: $latest_csv"

    tail -n +2 "$latest_csv" | while IFS=',' read -r id fecha nombre ciudad direccion correo telefono ip cantidad monto pago estado timestamp obs; do
        PDF="$FACTURAS/factura_${id}.pdf"
        LOG_FACTURA="$LOG_DIR/factura_${id}.log"
        TEX_TEMP="$SCRIPT_DIR/factura_${id}.tex"

        # Omitir si ya existe
        [ -f "$PDF" ] && echo "Factura existente para ID $id. Omitida." && continue

        # Escapar todos los campos
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

        echo "" | tee -a "$LOG_DIARIO"
        echo "Generando factura ID $id para $nombre" | tee -a "$LOG_DIARIO"

        # Crear archivo .tex personalizado
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

        # Compilar el .tex a PDF
        pdflatex -interaction=nonstopmode -output-directory="$FACTURAS" "$TEX_TEMP" > "$LOG_FACTURA" 2>&1

        # Validar si se generó correctamente
        if grep -q "^!" "$LOG_FACTURA"; then
            echo "ERROR: Falló la compilación para ID $id" | tee -a "$LOG_DIARIO"
            tail -n 5 "$LOG_FACTURA"
        elif [ -f "$PDF" ]; then
            echo "Factura generada: $PDF" | tee -a "$LOG_DIARIO"
            echo "factura_${id}.pdf,$correo" >> "$PENDIENTES"
        else
            echo "ADVERTENCIA: PDF no encontrado para ID $id" | tee -a "$LOG_DIARIO"
        fi

        # Limpiar temporales
        rm -f "$TEX_TEMP" "$FACTURAS/factura_${id}".{aux,log,out}

    done
else
    echo "No se encontraron archivos de compras para procesar." | tee -a "$LOG_DIARIO"
fi