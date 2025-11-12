# ... (código anterior de imports y configuración de Supabase)

# 🔐 Login y Registro (Si no existe)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_trabajo = request.form['id_trabajo']
        nombre = request.form['nombre']

        # 1. Buscar en tabla "cocinero" por id_trabajo y nombre
        response = supabase.table('cocinero').select('*').eq('id_trabajador', id_trabajo).eq('nombre', nombre).execute()
        
        usuario_actual = None

        if response.data:
            # Caso A: El usuario ya existe, lo usamos.
            usuario_actual = response.data[0]
            print(f"Usuario encontrado: {usuario_actual['nombre']}")
        else:
            # Caso B: El usuario NO existe, lo registramos (INSERT).
            # NOTA: Supabase/PostgreSQL requiere el 'turno' y 'especialidad' y 'correo'
            #       para la tabla Cocinero. Dado que no los pides en el formulario, 
            #       usaremos valores por defecto o simulados.
            
            # Buscamos si el id_trabajo ya existe pero con otro nombre
            id_check = supabase.table('cocinero').select('*').eq('id_trabajador', id_trabajo).execute()

            if id_check.data:
                # Si el id_trabajo existe pero el nombre no coincide, es un error de datos.
                return "⚠️ El ID de trabajo ya existe con otro nombre. Contacte al administrador."
            
            # Realizamos la inserción del nuevo usuario con datos predeterminados
            try:
                new_user_data = {
                    'id_trabajador': id_trabajo,
                    'nombre': nombre,
                    'fecha_ingreso': datetime.now().isoformat().split('T')[0], # Solo fecha
                    'turno': 'Sin Asignar', 
                    'correo': f'temp_{id_trabajo}@restaurante.com', # Correo temporal
                    'especialidad': 'General',
                    'años_experiencia': 0
                }
                
                insert_response = supabase.table('cocinero').insert(new_user_data).execute()
                
                if insert_response.data:
                    usuario_actual = insert_response.data[0]
                    print(f"Nuevo usuario registrado: {usuario_actual['nombre']}")
                else:
                    return "⚠️ Error al registrar el nuevo usuario en Supabase."

            except Exception as e:
                # Manejo de error si la inserción falla (ej. ID duplicado no serial)
                print(f"Error de Supabase: {e}")
                return "⚠️ Error de Supabase al intentar registrar el usuario."

        # Si tenemos un usuario (ya sea encontrado o recién creado)
        if usuario_actual:
            session['user'] = usuario_actual

            # Registrar el inicio en la tabla "asignacion_cocina" (como ya lo tenías)
            supabase.table('asignacion_cocina').insert({
                'id_cocinero': usuario_actual['id_trabajador'], # Usar el FK de cocinero
                'fecha_login': datetime.now().isoformat(),
                'estado': 'Activo',
                'id_pedido': 103, # NOTA: La tabla asignacion_cocina requiere 'id_pedido' y 'id_platillo'. 
                'id_platillo': 10 # Se usan IDs de prueba (103 y 10) para pasar la restricción de FK.
            }).execute()
            
            # Registrar el inicio en la tabla "Sesion_Cocinero"
            supabase.table('Sesion_Cocinero').insert({
                'id_cocinero': usuario_actual['id_trabajador'], 
                'fecha_login': datetime.now().isoformat(),
                'estado': 'Activo'
            }).execute()

            return redirect(url_for('index'))
        
        # Este punto no debería alcanzarse si todo va bien.
        return "⚠️ Datos incorrectos o usuario no encontrado/registrado."

    return render_template('login.html')

# ... (código de 'logout' y 'if __name__ == "__main__":')