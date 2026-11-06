from flask import Flask, flash, redirect, render_template, request, session, url_for

import banco

app = Flask(__name__)
app.secret_key = "studyup-chave-secreta"

CURSOS = [
    ("direito", "Direito"),
    ("sistemas", "Sistemas de Informação"),
    ("medicina", "Medicina"),
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mentores")
def mentores():
    return render_template("mentores.html", mentores=banco.listar_mentores())


@app.route("/vagas")
def vagas():
    return render_template("vagas.html", vagas=banco.listar_vagas())


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")
        curso = request.form.get("curso", "")

        if not (nome and email and senha and curso in dict(CURSOS)):
            flash("Preencha todos os campos.")
        elif senha != confirmar:
            flash("As senhas não conferem.")
        elif banco.cadastrar_usuario(nome, email, senha, curso) is None:
            flash("Este e-mail já está cadastrado.")
        else:
            flash("Conta criada! Faça login para continuar.")
            return redirect(url_for("login"))
    return render_template("cadastro.html", cursos=CURSOS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = banco.autenticar(request.form.get("email", ""), request.form.get("senha", ""))
        if usuario is None:
            flash("E-mail ou senha incorretos.")
        else:
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            flash(f"Bem-vindo, {usuario['nome']}!")
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    banco.criar_banco()
    app.run(debug=True)
