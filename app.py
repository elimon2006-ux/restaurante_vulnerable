from flask import Flask, render_template, request, redirect, session, url_for, flash
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---------------- SUPABASE ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- REGISTRO ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = {
            "nombre": request.form["nombre"],
            "correo": request.form["correo"],
            "telefono": request.form["telefono"],
            "contrasena": request.form["contrasena"],
            "calle": request.form["calle"],
            "numero": request.form["numero"],
            "colonia": request.form["colonia"],
            "ciudad": request.form["ciudad"],
        }

        supabase.table("clientes").insert(data).execute()
        flash("Registro exitoso. Ahora inicia sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contrasena"]

        user = (
            supabase.table("clientes")
            .select("*")
            .eq("correo", correo)
            .eq("contrasena", contrasena)
            .execute()
        )

        if len(user.data) == 1:
            session["user"] = user.data[0]
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas", "danger")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=session["user"])


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- MENÚ DE PLATILLOS ----------------

@app.route("/menu")
def menu():
    platillos = supabase.table("platillo").select("*").execute().data
    return render_template("menu.html", platillos=platillos)


# ---------------- PEDIDO ----------------

@app.route("/agregar_pedido", methods=["POST"])
def agregar_pedido():
    if "pedido" not in session:
        session["pedido"] = []

    platillo_id = request.form.get("id")
    nombre = request.form.get("nombre")
    precio = float(request.form.get("precio"))

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
    return render_template("mi_pedido.html", pedido=pedido, total=total)


# ---------------- MODIFICAR PEDIDO ----------------

@app.route("/modificar_pedido", methods=["POST"])
def modificar_pedido():
    accion = request.form.get("accion")
    platillo_id = request.form.get("id")
    pedido = session.get("pedido", [])

    for item in pedido:
        if item["id"] == platillo_id:
            if accion == "aumentar":
                item["cantidad"] += 1
            elif accion == "disminuir":
                item["cantidad"] -= 1
            elif accion == "eliminar":
                pedido.remove(item)
            break

    pedido = [i for i in pedido if i["cantidad"] > 0]
    session["pedido"] = pedido
    return redirect(url_for("mi_pedido"))


# ---------------- CONFIRMAR PEDIDO ----------------

@app.route("/confirmar_pedido", methods=["POST"])
def confirmar_pedido():
    pedido = session.get("pedido", [])
    if not pedido:
        flash("El carrito está vacío.", "danger")
        return redirect(url_for("menu"))

    id_cliente = session.get("user", {}).get("id_cliente")  # Cliente logueado
    total = sum(item["precio"] * item["cantidad"] for item in pedido)

    # Insertar en tabla pedido con fecha actual en timestamptz
    pedido_db = supabase.table("pedido").insert({
        "id_cliente": id_cliente,
        "total": total,
        "tipo_pedido": "Mesa",   # o "Domicilio"
        "estado": "PENDIENTE",
        "fecha": datetime.utcnow().isoformat()  # Fecha y hora UTC compatible con timestamptz
    }).execute()

    # Obtener id del pedido recién creado
    id_pedido = pedido_db.data[0]["id_pedido"]

    # Insertar detalles de pedido
    for item in pedido:
        supabase.table("detalle_pedido").insert({
            "id_pedido": id_pedido,
            "id_platillo": int(item["id"]),
            "cantidad": item["cantidad"],
            "precio_unitario": item["precio"]
        }).execute()

    session.pop("pedido")  # Limpiar carrito
    flash("Pedido confirmado con éxito!", "success")
    return redirect(url_for("menu"))


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True)

