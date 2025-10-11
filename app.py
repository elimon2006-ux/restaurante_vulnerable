import os
from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

@app.route('/')
def index():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        return "ERROR: La variable DATABASE_URL no está configurada.", 500
    
    conn = None
    # Valores por defecto para la plantilla HTML
    trabajadores = []  # <--- Esta lista almacenará todos los resultados
    estado_conexion = "ERROR"
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # -----------------------------------------------------------------
        # CONSULTA CLAVE: Seleccionar TODOS los trabajadores
        # -----------------------------------------------------------------
        cursor.execute("SELECT id_trabajador, nombre, turno FROM trabajador ORDER BY id_trabajador ASC")
        trabajadores = cursor.fetchall()  # <--- Recupera TODAS las filas
        
        estado_conexion = "CONEXIÓN Y LECTURA DE DATOS EXITOSA. "

    except Exception as e:
        estado_conexion = f"ERROR DE CONEXIÓN CRÍTICO: {e}"
        
    finally:
        if conn:
            conn.close() 

    # -----------------------------------------------------------------
    # PARTE CLAVE: Retornar la plantilla HTML (templates/index.html)
    # Pasando la lista completa de trabajadores.
    # -----------------------------------------------------------------
    return render_template('index.html', 
                           trabajadores=trabajadores,
                           estado=estado_conexion)