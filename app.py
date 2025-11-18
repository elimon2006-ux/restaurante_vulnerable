# app_vulnerable.py
# ----------------------------------------------------
# EJEMPLO INTENCIONALMENTE VULNERABLE (solo para demo)
# - NO USAR EN PRODUCCIÓN
# - Muestra malas prácticas: concatenación SQL, contraseñas en claro, etc.
# ----------------------------------------------------

from flask import Flask, render_template, request, redirect, session, url_for, flash
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

# Cargar .env con DATABASE_URL y SECRET_KEY
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_por_defecto_insegura")

# Conexión directa (sin pool) — también es parte de la "vulnerabilidad" por ineficiencia
def get_conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no definido en .env")
    # Se asume que DATABASE_URL es algo como:
    # postgresql://user:pass@host:port/dbname
    conn = psycopg2.connect(url, sslmode='require')
    return conn

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")  # asume template simple

# ---------------- REGISTRO (vulnerable) ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        correo = request.form.get("correo", "")
        telefono = request.form.get("telefono", "")
        contrasena = request.form.get("contrasena", "")  # en claro (malo)
        calle = request.form.get("calle", "")
        numero = request.form.get("numero", "")
        colonia = request.form.get("colonia", "")
        ciudad = request.form.get("ciudad", "")

        # INSERT construido por concatenación (vulnerable a SQL injection)
        sql = (
            "INSERT INTO clientes (nombre, correo, telefono, contrasena, calle, numero, colonia, ciudad, fecha_registro) "
            "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s');"
            % (nombre, correo, telefono, contrasena, calle, numero, colonia, ciudad, datetime.utcnow().isoformat())
        )

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(sql)   # ejecución de SQL construido con concatenación
            conn.commit()
            cur.close()
            conn.close()
            flash("Registro exitoso. Ahora inicia sesión.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            # Mostrar error crudo (inseguro para prod)
            flash(f"Error al registrar: {e}", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

# ---------------- LOGIN (vulnerable) ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "")
        contrasena = request.form.get("contrasena", "")

        # Consulta vulnerable con concatenación
        sql = (
            "SELECT id_cliente, nombre, correo, contrasena "
            "FROM clientes "
            "WHERE correo = '%s' AND contrasena = '%s';"
        ) % (correo, contrasena)

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(sql)   # VULNERABLE
            rows = cur.fetchall()   # ← AHORA OBTIENE TODAS LAS FILAS
            cur.close()
            conn.close()
        except Exception as e:
            flash(f"Error en login: {e}", "danger")
            return redirect(url_for("login"))

        # ------------------------------------------------------------------
        # Si la inyección hace efecto, 'rows' tendrá MUCHOS usuarios.
        # En lugar de iniciar sesión con uno, ahora lo mostramos.
        # ------------------------------------------------------------------
        if len(rows) > 1:
            # Mostrar lista filtrada (indicador de SQLi)
            return render_template("resultados.html", datos=rows, sql=sql)

        # Caso normal (sin inyección)
        if len(rows) == 1:
            row = rows[0]
            session["user"] = {
                "id_cliente": row[0],
                "nombre": row[1],
                "correo": row[2]
            }
            flash("Login exitoso", "success")
            return redirect(url_for("dashboard"))

        flash("Credenciales incorrectas", "danger")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])

# ---------------- MENU ----------------
@app.route("/menu")
def menu():
    try:
        conn = get_conn()
        cur = conn.cursor()
        # SELECT simple (aun vulnerable si concatenásemos filtros)
        cur.execute("SELECT id_platillo, nombre, descripcion, precio FROM platillo;")
        platillos = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Error cargando menú: {e}", "danger")
        platillos = []
    # Convertir a dicts básicos para templates
    platillos_list = [{"id": r[0], "nombre": r[1], "descripcion": r[2], "precio": float(r[3])} for r in platillos]
    return render_template("menu.html", platillos=platillos_list)

# ---------------- PEDIDO en sesión (vulnerable a manipulación cliente) ----------------
@app.route("/agregar_pedido", methods=["POST"])
def agregar_pedido():
    if "pedido" not in session:
        session["pedido"] = []

    try:
        platillo_id = int(request.form.get("id"))
        nombre = request.form.get("nombre")
        precio = float(request.form.get("precio"))  # precio confiado del cliente (vulnerable)
    except Exception:
        flash("Error al agregar el platillo.", "danger")
        return redirect(url_for("menu"))

    pedido = session["pedido"]
    for item in pedido:
        if item["id"] == platillo_id:
            item["cantidad"] += 1
            break
    else:
        pedido.append({"id": platillo_id, "nombre": nombre, "precio": precio, "cantidad": 1})

    session["pedido"] = pedido
    flash(f"{nombre} agregado al pedido", "success")
    return redirect(url_for("menu"))

# ---------------- MI PEDIDO ----------------
@app.route("/mi_pedido")
def mi_pedido():
    pedido = session.get("pedido", [])
    total = sum(item["precio"] * item["cantidad"] for item in pedido)
    # No se validan fechas ni origenes
    return render_template("mi_pedido.html", pedido=pedido, total=total)

# ---------------- CONFIRMAR PEDIDO (vulnerable) ----------------
@app.route("/confirmar_pedido", methods=["POST"])
def confirmar_pedido():
    pedido = session.get("pedido", [])
    if not pedido:
        flash("El carrito está vacío.", "danger")
        return redirect(url_for("menu"))

    user = session.get("user")
    if not user:
        flash("Debes iniciar sesión.", "danger")
        return redirect(url_for("login"))

    id_cliente = user.get("id_cliente")

    total = sum(item["precio"] * item["cantidad"] for item in pedido)
    fecha_actual = datetime.now(ZoneInfo("America/Mexico_City")).isoformat()

    # INSERT vulnerable por concatenación
    sql_pedido = "INSERT INTO pedido (id_cliente, total, tipo_pedido, fecha) VALUES (%s, %s, '%s', '%s') RETURNING id_pedido;" % (
        id_cliente, total, "Mesa", fecha_actual
    )

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql_pedido)
        id_pedido = cur.fetchone()[0]

        # Insertar detalles vulnerable (concatenación)
        for item in pedido:
            sql_det = "INSERT INTO detalle_pedido (id_pedido, id_platillo, cantidad, precio_unitario) VALUES (%s, %s, %s, %s);" % (
                id_pedido, item["id"], item["cantidad"], item["precio"]
            )
            cur.execute(sql_det)

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Error guardando pedido: {e}", "danger")
        return redirect(url_for("mi_pedido"))

    session.pop("pedido", None)
    flash("Pedido confirmado con éxito!", "success")
    return redirect(url_for("menu"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)