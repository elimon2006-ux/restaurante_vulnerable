from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__)
# RECUERDA: Clave secreta para cifrar sesiones. Cambia este valor por tu propia clave aleatoria para producción.
app.secret_key = os.getenv("SECRET_KEY", "b3a5c8e0d1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8") 

# 🔧 Configuracion de Supabase
# Asegurate de reemplazar "TU_API_KEY" con la clave publica (anon) de tu proyecto
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cwyjhnxowglgqbqzshyd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3dmpobnhvd2dsZ3FicXpzaHlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAxMDE0NTQsImV4cCI6MjA3NTY3NzQ1NH0.lbW8TGXa7_WFoFeWE6Vfgt3kl2SdnyFt3Dv_vhgw1Qw") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Pagina principal
@app.route('/')
def index():
    if "user" in session:
        usuario = session["user"]
        # Pasa el objeto usuario (que contiene 'id_trabajador', 'nombre', etc.) al template
        return render_template("index.html", usuario=usuario) 
    return redirect(url_for('login'))


# Login y Registro (Si no existe, se registra como nuevo cocinero)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # El formulario HTML envia 'id_trabajo', lo asignamos al nombre de columna correcto
        id_input = request.form['id_trabajo']
        nombre = request.form['nombre']
        
        usuario_actual = None

        # 1. Buscar en tabla "cocinero" usando el nombre de columna correcto: 'id_trabajador'
        try:
            response = supabase.table('cocinero').select('*').eq('id_trabajador', id_input).eq('nombre', nombre).execute()
        except Exception as e:
            # Error critico al hacer la consulta SELECT (probablemente clave de API o URL incorrecta)
            print(f"ERROR CRÍTICO (SELECT): {e}")
            return f"⚠️ Error de conexion a Supabase al buscar usuario. Revise URL/Key. Error: {e}"

        
        if response.data:
            # Caso A: El usuario ya existe, lo usamos.
            usuario_actual = response.data[0]
            print(f"DEBUG: Usuario encontrado: {usuario_actual.get('nombre')}")
        else:
            # Caso B: El usuario NO existe, intentamos registrarlo.
            
            # Chequeo si el ID ya existe con otro nombre (para evitar error de integridad)
            id_check = supabase.table('cocinero').select('nombre').eq('id_trabajador', id_input).execute()
            if id_check.data:
                return "⚠️ El ID de trabajo ya existe con otro nombre. Contacte al administrador."

            try:
                # Proveemos valores NOT NULL requeridos por tu esquema SQL:
                new_user_data = {
                    'id_trabajador': id_input,
                    'nombre': nombre,
                    'fecha_ingreso': datetime.now().isoformat().split('T')[0],
                    'turno': 'Sin Asignar', 
                    'correo': f'temp_{id_input}_{datetime.now().strftime("%H%M%S")}@restaurante.com', 
                    'especialidad': 'General',
                    'años_experiencia': 0
                }
                
                insert_response = supabase.table('cocinero').insert(new_user_data).execute()
                
                if insert_response.data:
                    usuario_actual = insert_response.data[0]
                    print(f"DEBUG: Nuevo usuario registrado: {usuario_actual.get('nombre')}")
                else:
                    return "⚠️ Error al registrar el nuevo usuario en Supabase (respuesta vacia)."

            except Exception as e:
                # Si esto falla, el problema es RLS o falta de la tabla.
                print(f"ERROR CRÍTICO (INSERT): Fallo el INSERT en Cocinero: {e}")
                return f"⚠️ Error de Supabase al registrar. Revise RLS y la tabla Cocinero. Error: {e}"


        # Si tenemos un usuario (encontrado o recien creado)
        if usuario_actual:
            session['user'] = usuario_actual

            # 2. Registrar el inicio en la tabla de sesiones (Sesion_Cocinero)
            try:
                supabase.table('Sesion_Cocinero').insert({
                    'id_cocinero': usuario_actual['id_trabajador'], 
                    'fecha_login': datetime.now().isoformat(),
                    'estado': 'Activo'
                }).execute()
            except Exception as e:
                # Esto es un warning. El login es exitoso, pero la sesion no se registro en BD.
                print(f"WARNING: Fallo el registro en Sesion_Cocinero. Asegurese de que la tabla exista. {e}") 
            
            return redirect(url_for('index'))
        
        # Fallback
        return "⚠️ Datos incorrectos o usuario no encontrado/registrado."

    return render_template('login.html')


# Cerrar sesion
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)