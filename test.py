import os
import redis
from dotenv import load_dotenv

print("Iniciando prueba de conexión a Redis...")

# Cargar las variables de entorno desde el archivo .env
# Esto simula lo que hace tu aplicación al arrancar.
load_dotenv()

# Obtener la URL de Redis del entorno
redis_url =  os.environ.get("REDIS_URL")

if not redis_url:
    print("\nERROR: No se encontró la variable REDIS_URL.")
    print("Asegúrate de que tu archivo .env está en la misma carpeta y contiene la línea REDIS_URL=...")
else:
    print(f"URL de Redis encontrada: {redis_url}") # Muestra solo el inicio de la URL por seguridad
    
    try:
        # Intentar conectar a Redis.
        # Upstash usa SSL, la librería de redis en Python lo maneja automáticamente
        # con las URLs que empiezan con "rediss://" o "redis://" con --tls.
        # Tu URL de Upstash debería funcionar directamente.
        client = redis.from_url(redis_url)

        # Enviar un comando PING para verificar la conexión y la autenticación.
        response = client.ping()

        if response:
            print("\n¡ÉXITO! La conexión con Redis (Upstash) funciona correctamente.")
            print("Respuesta del servidor: PONG")
        else:
            print("\nERROR: La conexión se estableció, pero el comando PING falló.")

    except redis.exceptions.AuthenticationError:
        print("\nERROR DE AUTENTICACIÓN: La contraseña es incorrecta.")
        print("Verifica que la URL en tu archivo .env sea la correcta y que la credencial esté activa en Upstash.")
        
    except redis.exceptions.ConnectionError as e:
        print(f"\nERROR DE CONEXIÓN: No se pudo conectar a Redis.")
        print(f"Detalle del error: {e}")
        print("Verifica que la URL sea correcta y que no haya un firewall bloqueando la conexión.")
        
    except Exception as e:
        print(f"\nHA OCURRIDO UN ERROR INESPERADO: {e}")