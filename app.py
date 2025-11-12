from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_super_secreta")

# 🔧 Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cwyjhnxowglgqbqzshyd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "TU_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🏠 Página principal
@app.route('/')
def index():
    if "user" in session:
        usuario = session["user"]
        return render_template("index.html", usuario=usuario)
    return redirect(url_for('login'))


# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_trabajo = request.form['id_trabajo']
        nombre = request.form['nombre']

        # Buscar en tabla "cocinero"
        response = supabase.table('cocinero').select('*').eq('id_trabajo', id_trabajo).eq('nombre', nombre).execute()

        if response.data:
            session['user'] = response.data[0]

            # Registrar el inicio en la tabla "asignacion_cocina"
            supabase.table('asignacion_cocina').insert({
                'id_trabajo': id_trabajo,
                'fecha_login': datetime.now().isoformat(),
                'estado': 'Activo'
            }).execute()

            return redirect(url_for('index'))
        else:
            return "⚠️ Datos incorrectos o usuario no encontrado."

    return render_template('login.html')


# 🚪 Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
