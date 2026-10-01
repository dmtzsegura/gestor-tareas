from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.secret_key = "1234"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
db = SQLAlchemy(app)


class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    usuario = db.relationship("Usuario")
    estatus = db.Column(db.String(20), default="Pendiente")
    fecha_asignacion = db.Column(db.Date, nullable=False)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)


@app.route("/")
def home():
    filtro_usuario_id = request.args.get("usuario_id")

    if filtro_usuario_id:
        tareas = Tarea.query.filter_by(usuario_id=int(filtro_usuario_id)).all()
    else:
        tareas = Tarea.query.all()

    for tarea in tareas:
        tarea.dias_transcurridos = (date.today() - tarea.fecha_asignacion).days

    return render_template("index.html", tareas=tareas, filtro_usuario_id=filtro_usuario_id, usuarios=Usuario.query.all())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre"]
        password = request.form["password"]
        usuario = Usuario.query.filter_by(nombre=nombre, password=password).first()
        
        if usuario:
            session["usuario"] = usuario.nombre
            return redirect(url_for("home"))
        
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
        
    return render_template("login.html")    
        

@app.route("/nueva", methods=["GET", "POST"])
def nueva_tarea():
    if request.method == "POST":
        titulo = request.form["titulo"]
        usuario_id = int(request.form["usuario_id"])

        if not titulo.strip() or not usuario_id:
            m_error = "No puedes dejar campos vacíos"
            return render_template("nueva_tarea.html", error=m_error, usuarios=Usuario.query.all())

        else:
            tarea = Tarea(titulo=titulo, usuario_id=usuario_id, fecha_asignacion=date.today())
            db.session.add(tarea)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("nueva_tarea.html", usuarios=Usuario.query.all())

@app.route("/actualizar_estatus/<int:tarea_id>", methods=["POST"])
def actualizar_estatus(tarea_id):
    tarea = Tarea.query.get(tarea_id)
    tarea.estatus = request.form["estatus"]
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/editar/<int:tarea_id>", methods=["GET", "POST"])
def editar_tarea(tarea_id):
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
    tarea = Tarea.query.get_or_404(tarea_id)
    db.session.delete(tarea)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)





