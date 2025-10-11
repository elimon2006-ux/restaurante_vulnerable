import os
from flask import Flask, render_template # Importamos render_template
import psycopg2

app = Flask(__name__)

@app.route('/')
def index():
    # Leer la URL de la base de datos desde la variable de entorno de Render
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        # Si la variable no existe, devuelve un error.
        return "ERROR: La variable DATABASE_URL no está configurada.", 500
    
    conn = None
    # Valores por defecto para la plantilla HTML
    nombre_trabajador = "N/A - Trabajador no insertado"
    turno_trabajador = "N/A"
    estado_conexion = "ERROR"
    
    try:
        # Intenta conectar a Supabase
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Consulta para OBTENER los datos del trabajador con ID=1
        cursor.execute("SELECT nombre, turno FROM trabajador WHERE id_trabajador = 1")
        trabajador = cursor.fetchone() 

        cursor.execute("SELECT nombre, tunro FROM trabajador Where id_trabajador  = 2")
        trabajador = cursor.fetchone() 

        if trabajador:
            # Asigna los valores a las variables de la plantilla:
            nombre_trabajador = trabajador[0]
            turno_trabajador = trabajador[1]
            estado_conexion = "CONEXIÓN Y LECTURA DE DATOS EXITOSA. 🎉"
        else:
            estado_conexion = "CONEXIÓN EXITOSA, PERO NO SE ENCONTRÓ EL TRABAJADOR ID=1."

    except Exception as e:
        estado_conexion = f"ERROR DE CONEXIÓN CRÍTICO: {e}"
        
    finally:
        if conn:
            conn.close() # Cierra la conexión de forma segura

    # -----------------------------------------------------------------
    # PARTE CLAVE: Retornar la plantilla HTML (templates/index.html)
    # -----------------------------------------------------------------
    # Flask buscará 'index.html' en la carpeta 'templates' 
    # y le pasará las variables que creamos para que las muestre.
    return render_template('index.html', 
                           nombre=nombre_trabajador,
                           turno=turno_trabajador,
                           estado=estado_conexion)

# Nota: No se incluye if __name__ == '__main__': porque Gunicorn lo maneja.