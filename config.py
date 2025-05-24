# config.py - Archivo de configuración con variables de entorno
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración desde variables de entorno
BOT_TOKEN = os.getenv('BOT_TOKEN', '7589496460:AAFR4tKNT3cSAX4pc55x6uaqEdMA2oc1hFI')
GRUPO_PEDIDOS_ID = os.getenv('GRUPO_PEDIDOS_ID', '-1002541246940')
ADMIN_ID = os.getenv('ADMIN_ID', '5979848389')

# Para desarrollo local (opcional)
if BOT_TOKEN == 'TU_TOKEN_AQUI':
    print("⚠️ CONFIGURAR VARIABLES DE ENTORNO EN RAILWAY")
    print("BOT_TOKEN, GRUPO_PEDIDOS_ID, ADMIN_ID")
