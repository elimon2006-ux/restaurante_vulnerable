import os
from flask import Flask, render_template_string
import psycopg2

app = Flask(__name__)

# ... código inicial ...

@app.route('/')
def index():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # ... manejo de errores ...
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Consulta para OBTENER los datos que insertaste
        cursor.execute("SELECT nombre, turno FROM trabajador WHERE id_trabajador = 1")
        trabajador = cursor.fetchone() # recupera la primera fila de la consulta
        
        if trabajador:
            # Asigna una tupla de datos a la variable 'resultado'
            resultado = (trabajador[0], trabajador[1]) # ej: ('Andrea Gomez', 'Matutino')
        else:
            resultado = ("No se encontraron datos", "Asegúrate de que el id_trabajador=1 exista.")

    except Exception as e:
        resultado = (f"Error al conectar o consultar la BD: {e}", "Revisa tus tablas.")
        
    finally:
        if conn:
            conn.close()

    # Pasa la variable 'resultado' que contiene los datos a la plantilla HTML
    # ...

    # Muestra el resultado en una página simple
   # Muestra el resultado en una página simple
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>App Restaurante</title></head>
    <body>
        <h1>Sistema de Pedidos del Restaurante</h1>
        <h2>Datos del Trabajador de Prueba (ID 1)</h2>
        
        <p><strong>Estado del Servicio:</strong> Conexión a Base de Datos Exitosa!</p>
        
        <p><strong>Nombre del Trabajador:</strong> {resultado[0]}</p>
        <p><strong>Turno Asignado:</strong> {resultado[1]}</p>
        
        <hr>
        <p>¡El siguiente paso es crear la interfaz de usuario para los pedidos!</p>
    </body>
    </html>
    """
    return render_template_string(html_content)