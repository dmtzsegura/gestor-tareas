from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date

import unicodedata

def quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

app = Flask(__name__)
app.secret_key = "1234"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
db = SQLAlchemy(app)


class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    usuario = db.relationship("Usuario", foreign_keys=[usuario_id])
    creado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    creado_por = db.relationship("Usuario", foreign_keys=[creado_por_id])
    estatus = db.Column(db.String(20), default="Pendiente")
    fecha_asignacion = db.Column(db.Date, nullable=False)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)


@app.route("/")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    
    filtro_usuario_id = request.args.get("usuario_id")

    if filtro_usuario_id:
        tareas = Tarea.query.filter_by(usuario_id=int(filtro_usuario_id)).all()
    else:
        tareas = Tarea.query.all()

    for tarea in tareas:
        tarea.dias_transcurridos = (date.today() - tarea.fecha_asignacion).days
        
    total = len(tareas)
    pendientes = len([t for t in tareas if t.estatus == "Pendiente"])
    en_proceso = len([t for t in tareas if t.estatus == "En proceso"])
    completadas = len([t for t in tareas if t.estatus == "Completado"])

    return render_template("index.html", tareas=tareas, filtro_usuario_id=filtro_usuario_id, usuarios=Usuario.query.all(), total=total, pendientes=pendientes, en_proceso=en_proceso, completadas=completadas)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre"]
        password = request.form["password"]
        nombre_normalizado = quitar_acentos(nombre).lower()
        usuario = None
        for u in Usuario.query.all():
            if quitar_acentos(u.nombre).lower() == nombre_normalizado and u.password == password:
                usuario = u
                break
        
        if usuario:
            session["usuario"] = usuario.nombre
            return redirect(url_for("home"))
        
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
        
    return render_template("login.html")    
        

@app.route("/nueva", methods=["GET", "POST"])
def nueva_tarea():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form["titulo"]
        usuario_id = int(request.form["usuario_id"])

        if not titulo.strip() or not usuario_id:
            m_error = "No puedes dejar campos vacíos"
            return render_template("nueva_tarea.html", error=m_error, usuarios=Usuario.query.all())

        else:
            usuario_actual = Usuario.query.filter_by(nombre=session["usuario"]).first()
            tarea = Tarea(titulo=titulo, usuario_id=usuario_id, creado_por_id=usuario_actual.id, fecha_asignacion=date.today())
            db.session.add(tarea)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("nueva_tarea.html", usuarios=Usuario.query.all())


@app.route("/actualizar_estatus/<int:tarea_id>", methods=["POST"])

def actualizar_estatus(tarea_id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    
    usuario_actual = Usuario.query.filter_by(nombre=session["usuario"]).first()
    tarea = Tarea.query.get(tarea_id)
    nuevo_estatus = request.form["estatus"]
    
    if nuevo_estatus == "En proceso" and (usuario_actual.id == tarea.usuario_id or usuario_actual.id == tarea.creado_por_id):
        tarea.estatus = nuevo_estatus
        
    elif nuevo_estatus == "Completado" and usuario_actual.id == tarea.creado_por_id:
        tarea.estatus = nuevo_estatus

    elif nuevo_estatus == "Pendiente" and usuario_actual.id == tarea.creado_por_id:
        tarea.estatus = nuevo_estatus

    else:
        flash("Solo quién te asignó la tarea tiene permiso para realizar este cambio")
        
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/editar/<int:tarea_id>", methods=["GET", "POST"])
def editar_tarea(tarea_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    tarea = Tarea.query.get_or_404(tarea_id)
    if request.method == "POST":
        titulo = request.form["titulo"]
        usuario_id = int(request.form["usuario_id"])

        if not titulo.strip() or not usuario_id:
            m_error = "No puedes dejar campos vacíos"
            return render_template("editar_tarea.html", error=m_error, tarea=tarea, usuarios=Usuario.query.all())
        else:
            tarea.titulo = titulo
            tarea.usuario_id = usuario_id
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("editar_tarea.html", tarea=tarea, usuarios=Usuario.query.all())

@app.route("/eliminar/<int:tarea_id>", methods=["POST"])
def eliminar_tarea(tarea_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario_actual = Usuario.query.filter_by(nombre=session["usuario"]).first()
    tarea = Tarea.query.get_or_404(tarea_id)

    if usuario_actual.id == tarea.creado_por_id:
        db.session.delete(tarea)
        db.session.commit()
    else:
        flash("Sólo quién asignó la tarea tiene permiso para eliminarla")

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)





