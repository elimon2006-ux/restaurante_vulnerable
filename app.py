from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__)
# ¡IMPORTANTE! Cambia esta clave en producción
app.secret_key = os.getenv("SECRET_KEY", "clave_super_secreta") 

# 🔧 Configuración de Supabase
# Asegúrate de reemplazar estos valores con los de tu proyecto
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cwyjhnxowglgqbqzshyd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "TU_API_KEY") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🏠 Página principal
@app.route('/')
def index():
    if "user" in session:
        usuario = session["user"]
        # Nota: Usamos 'id_trabajador' porque así se llama el campo en la tabla Cocinero
        return render_template("index.html", usuario=usuario) 
    return redirect(url_for('login'))


# 🔐 Login y Registro (Si no existe, se registra como nuevo cocinero)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_trabajador = request.form['id_trabajo'] # El input del formulario se llama 'id_trabajo'
        nombre = request.form['nombre']
        
        usuario_actual = None

        # 1. Buscar en tabla "cocinero" por id_trabajador y nombre
        # Nota: El campo correcto en tu DB es 'id_trabajador'
        response = supabase.table('cocinero').select('*').eq('id_trabajador', id_trabajador).eq('nombre', nombre).execute()
        
        if response.data:
            # Caso A: El usuario ya existe, lo usamos.
            usuario_actual = response.data[0]
            print(f"DEBUG: Usuario encontrado: {usuario_actual['nombre']}")
        else:
            # Caso B: El usuario NO existe, intentamos registrarlo.

            # Buscamos si el ID ya existe solo para dar un mejor mensaje de error
            id_check = supabase.table('cocinero').select('*').eq('id_trabajador', id_trabajador).execute()
            if id_check.data:
                return "⚠️ El ID de trabajo ya existe con otro nombre o datos. Contacte al administrador."

            # Realizamos la inserción del nuevo usuario con datos temporales/por defecto
            try:
                # Datos requeridos por la tabla Cocinero (NOT NULL)
                new_user_data = {
                    'id_trabajador': id_trabajador,
                    'nombre': nombre,
                    'fecha_ingreso': datetime.now().isoformat().split('T')[0],
                    'turno': 'Sin Asignar', 
                    'correo': f'temp_{id_trabajador}@restaurante.com', 
                    'especialidad': 'General',
                    'años_experiencia': 0
                }
                
                insert_response = supabase.table('cocinero').insert(new_user_data).execute()
                
                if insert_response.data:
                    usuario_actual = insert_response.data[0]
                    print(f"DEBUG: Nuevo usuario registrado: {usuario_actual['nombre']}")
                else:
                    return "⚠️ Error al registrar el nuevo usuario en Supabase."

            except Exception as e:
                print(f"ERROR: Falló el INSERT en Cocinero: {e}")
                return "⚠️ Error de Supabase al intentar registrar el usuario. Revisa el RLS o las restricciones."


        # Si tenemos un usuario (ya sea encontrado o recién creado)
        if usuario_actual:
            session['user'] = usuario_actual

            # 2. Registrar el inicio en la nueva tabla de sesiones (Sesion_Cocinero)
            # REQUISITO: DEBES CREAR LA TABLA Sesion_Cocinero EN SUPABASE
            try:
                supabase.table('Sesion_Cocinero').insert({
                    'id_cocinero': usuario_actual['id_trabajador'], 
                    'fecha_login': datetime.now().isoformat(),
                    'estado': 'Activo'
                }).execute()
                print("DEBUG: Sesión registrada correctamente.")
            except Exception as e:
                print(f"ERROR: Falló el registro en Sesion_Cocinero: {e}")
                # El login continua aunque falle el registro de sesión
            
            return redirect(url_for('index'))
        
        # Fallback si no se encontró ni se pudo registrar
        return "⚠️ Datos incorrectos o usuario no encontrado/registrado."

    return render_template('login.html')


# 🚪 Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Usamos 127.0.0.1 en lugar de 0.0.0.0 para entornos de desarrollo local
    app.run(host='127.0.0.1', port=5000, debug=True)