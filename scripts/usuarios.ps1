# Configuración inicial
param(
    [string]$csvPath = "$PSScriptRoot/../data/empleados/empleados.csv",
    [string]$logFolder = "$PSScriptRoot/../data/logs/logs_usuarios",
    [string]$dominioCorreo = "proyectoScripting.com"
)

# Crear estructura de carpetas si no existe
if (-not (Test-Path $logFolder)) {
    New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
}

# Definir nombres de archivos con fecha
$currentDate = Get-Date -Format "yyyyMMdd"
$logFile = "$logFolder/usuarios_$currentDate.log"

# Función para generar contraseñas seguras
function New-SecurePassword {
    $length = 12
    $nonAlphaChars = 3
    $password = [System.Web.Security.Membership]::GeneratePassword($length, $nonAlphaChars)
    return $password
}

# Función para crear usuarios
function New-TemporaryUser {
    param(
        [PSCustomObject]$userData
    )

    try {
        # Generar nombre de usuario (primera letra del nombre + apellido)
        $username = ($userData.Nombre.Substring(0,1) + $userData.Apellido)
        $username = $username.ToLower()
        $username = $username -replace 'á', 'a'
        $username = $username -replace 'é', 'e'
        $username = $username -replace 'í', 'i'
        $username = $username -replace 'ó', 'o'
        $username = $username -replace 'ú', 'u'
        $username = $username -replace '[^a-z]', ''
        
        # Verificar si el usuario ya existe
        if (Get-LocalUser -Name $username -ErrorAction SilentlyContinue) {
            Write-Log "El usuario $username ya existe. Se agregará un número al final."
            $i = 1
            while (Get-LocalUser -Name "$username$i" -ErrorAction SilentlyContinue) {
                $i++
            }
            $username = "$username$i"
        }

        # Generar contraseña segura
        $password = New-SecurePassword
        $securePassword = ConvertTo-SecureString $password -AsPlainText -Force

        # Crear el usuario
        New-LocalUser -Name $username `
                      -FullName "$($userData.Nombre) $($userData.Apellido)" `
                      -Password $securePassword `
                      -Description "Usuario temporal - $($userData.Departamento)" `
                      -ErrorAction Stop

        # Agregar al grupo de Administradores si es necesario
        if ($userData.Privilegios -eq "Admin") {
            Add-LocalGroupMember -Group "Administradores" -Member $username -ErrorAction SilentlyContinue
        }

        # Generar correo institucional
        $email = "$username@$dominioCorreo"

        # Retornar objeto con la información del usuario creado
        return [PSCustomObject]@{
            Username      = $username
            FullName      = "$($userData.Nombre) $($userData.Apellido)"
            Email         = $email
            Password      = $password
            Department    = $userData.Departamento
            Privileges    = $userData.Privilegios
            Status        = "Created"
            ErrorMessage = ""
        }
    }
    catch {
        return [PSCustomObject]@{
            Username      = $username
            FullName      = "$($userData.Nombre) $($userData.Apellido)"
            Email         = ""
            Password      = ""
            Department    = $userData.Departamento
            Privileges    = $userData.Privilegios
            Status        = "Failed"
            ErrorMessage = $_.Exception.Message
        }
    }
}

# Función para escribir en el log
function Write-Log {
    param(
        [string]$message,
        [string]$level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp][$level] $message"
    Add-Content -Path $logFile -Value $logEntry

    # Mostrar en consola también
    Write-Host $logEntry
}

# Función principal
function Main {
    # Verificar si el script se está ejecutando como administrador
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Log "Este script requiere privilegios de administrador. Por favor, ejecútalo como administrador." -level "ERROR"
        exit 1
    }

    Write-Log "Iniciando proceso de creación de usuarios temporales"
    Write-Log "Leyendo archivo CSV: $csvPath"

    # Verificar si el archivo CSV existe
    if (-not (Test-Path $csvPath)) {
        Write-Log "El archivo $csvPath no existe. Por favor, proporcione un archivo CSV válido." -level "ERROR"
        exit 1
    }

    try {
        # Importar datos del CSV
        $empleados = Import-Csv -Path $csvPath -Delimiter "," -Encoding UTF8
        
        # Validar estructura del CSV
        $requiredFields = @("Nombre", "Apellido", "Departamento", "Privilegios")
        foreach ($field in $requiredFields) {
            if (-not ($empleados[0].PSObject.Properties.Name -contains $field)) {
                throw "El archivo CSV no tiene el campo requerido: $field"
            }
        }

        Write-Log "Se encontraron $($empleados.Count) empleados para procesar"

        # Procesar cada empleado
        $results = @()
        foreach ($empleado in $empleados) {
            Write-Log "Procesando usuario: $($empleado.Nombre) $($empleado.Apellido)"
            $result = New-TemporaryUser -userData $empleado
            $results += $result

            if ($result.Status -eq "Created") {
                Write-Log "Usuario $($result.Username) creado exitosamente"
            } else {
                Write-Log "Error al crear usuario: $($result.ErrorMessage)" -level "ERROR"
            }
        }

        # Mostrar resumen en consola
        $successCount = ($results | Where-Object { $_.Status -eq 'Created' }).Count
        $errorCount = ($results | Where-Object { $_.Status -eq 'Failed' }).Count

        Write-Host "Usuarios procesados: $results" -ForegroundColor White
        Write-Host "Usuarios creados: $successCount" -ForegroundColor Green
        Write-Host "Errores: $errorCount" -ForegroundColor Red

        if ($errorCount -gt 0) {
            Write-Host "`nDetalle de errores:`n" -ForegroundColor Yellow
            $results | Where-Object { $_.Status -eq 'Failed' } | Format-Table Username, FullName, ErrorMessage -AutoSize
        }

        Write-Log "Proceso completado. $successCount usuarios creados, $errorCount errores."
    }
    catch {
        Write-Log "Error en el proceso principal: $($_.Exception.Message)" -level "ERROR"
        exit 1
    }
}

# Ejecutar función principal
Main