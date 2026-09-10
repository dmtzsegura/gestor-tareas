from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
db = SQLAlchemy(app)


class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    responsable = db.Column(db.String(50), nullable=False)
    estatus = db.Column(db.String(20), default="Pendiente")
    fecha_asignacion = db.Column(db.Date, nullable=False)


@app.route("/")
def home():
    tareas = Tarea.query.all()
    return render_template("index.html", tareas=tareas)

@app.route("/nueva", methods=["GET", "POST"])
def nueva_tarea():
    if request.method == "POST":
        titulo = request.form["titulo"]
        responsable = request.form["responsable"]

        tarea = Tarea(titulo=titulo, responsable=responsable, fecha_asignacion=date.today())
        db.session.add(tarea)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("nueva_tarea.html")

if __name__ == "__main__":
    app.run(debug=True)

