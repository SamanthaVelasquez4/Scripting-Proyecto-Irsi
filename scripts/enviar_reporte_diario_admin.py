"""
    Este script puede ser ejecutado manualmente o programado con `TaskScheduler` para
    enviar reportes diarios de forma automática.
"""
from enviador import almacenar_log_diario

if __name__ == "__main__":
    almacenar_log_diario(enviar=True)