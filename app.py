import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psycopg2
from flask import Flask, redirect, render_template, request, session
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# ---------------------------------------------------------------------------
# Configuration (all sensitive values come from environment variables)
# ---------------------------------------------------------------------------

ADMINS = [name.strip().lower() for name in os.environ.get("ADMIN_USERS", "").split(",") if name.strip()]
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5521970201569")

DATABASE_URL = os.environ.get("DATABASE_URL", "")

UPLOAD_FOLDER = os.path.join("static", "curriculos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS freelancers (
                    id          SERIAL PRIMARY KEY,
                    nome        VARCHAR(100),
                    profissao   VARCHAR(50),
                    cidade      VARCHAR(50),
                    telefone    VARCHAR(20),
                    email       VARCHAR(100),
                    score       DECIMAL(2,1) DEFAULT 5.0,
                    curriculo   VARCHAR(200),
                    situacao    VARCHAR(20)
                )
            """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS avaliacoes (
                    id            SERIAL PRIMARY KEY,
                    freelancer_id INTEGER REFERENCES freelancers(id) ON DELETE CASCADE,
                    nota          INTEGER,
                    comentario    TEXT
                )
            """
            )
        conn.commit()


init_db()

# ---------------------------------------------------------------------------
# Email helper
# ---------------------------------------------------------------------------


def send_selection_email(recipient: str, name: str) -> bool:
    """Send a selection notification e-mail to the freelancer."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = recipient
        msg["Subject"] = "Você foi selecionado! — Sidec Corporate"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 30px;">
            <div style="background: white; border-radius: 10px; padding: 30px;
                        max-width: 500px; margin: auto;">
                <h2 style="color: #d97706;">Olá, {name}! 👋</h2>
                <p style="font-size: 15px; color: #444; line-height: 1.6;">
                    Temos uma ótima notícia — você foi selecionado pela nossa equipe!
                </p>
                <p style="font-size: 15px; color: #444; line-height: 1.6;">
                    📱 <strong>Entre em contato conosco pelo WhatsApp</strong> —
                    vamos te passar todos os detalhes por lá.
                </p>
                <div style="text-align: center; margin: 24px 0;">
                    <a href="https://wa.me/{WHATSAPP_NUMBER}"
                       style="background: #25d366; color: white; padding: 12px 28px;
                              border-radius: 8px; text-decoration: none;
                              font-size: 16px; font-weight: bold;">
                        💬 Falar no WhatsApp
                    </a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
                <p style="font-size: 12px; color: #aaa; text-align: center;">
                    Sidec Corporate
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as exc:
        app.logger.error("Failed to send e-mail: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def is_logged_in() -> bool:
    return bool(session.get("logado"))


# ---------------------------------------------------------------------------
# Routes — public
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form["nome"]
    profissao = request.form["profissao"]
    cidade = request.form["cidade"]
    telefone = request.form["telefone"]
    email = request.form["email"]
    situacao = request.form["situacao"]

    curriculo_nome = None
    uploaded = request.files.get("curriculo")
    if uploaded and uploaded.filename:
        curriculo_nome = secure_filename(uploaded.filename)
        uploaded.save(os.path.join(UPLOAD_FOLDER, curriculo_nome))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO freelancers
                    (nome, profissao, cidade, telefone, email, curriculo, situacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (nome, profissao, cidade, telefone, email, curriculo_nome, situacao),
            )
        conn.commit()

    return render_template("cadastro.html", sucesso=True)


# ---------------------------------------------------------------------------
# Routes — auth
# ---------------------------------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()
        senha = request.form["senha"]
        if usuario in ADMINS and senha == ADMIN_PASSWORD:
            session["logado"] = True
            return redirect("/buscar")
        erro = "Usuário ou senha incorretos!"
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------------------------------------------------------------------
# Routes — admin (login required)
# ---------------------------------------------------------------------------


@app.route("/buscar")
def buscar():
    if not is_logged_in():
        return redirect("/login")

    profissao = request.args.get("profissao", "")
    mensagem = request.args.get("mensagem", "")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT nome, profissao, cidade, telefone, score, id, curriculo, situacao
                FROM freelancers
                WHERE profissao ILIKE %s
                ORDER BY score DESC
            """,
                (f"%{profissao}%",),
            )
            resultados = cur.fetchall()

    return render_template(
        "resultados.html",
        resultados=resultados,
        profissao=profissao,
        mensagem=mensagem,
    )


@app.route("/convocar/<int:freelancer_id>")
def convocar(freelancer_id: int):
    if not is_logged_in():
        return redirect("/login")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome, email FROM freelancers WHERE id = %s", (freelancer_id,)
            )
            freela = cur.fetchone()

    if not freela:
        return redirect("/buscar?mensagem=Freelancer não encontrado.")
    if not freela[1]:
        return redirect("/buscar?mensagem=Freelancer sem e-mail cadastrado.")

    success = send_selection_email(freela[1], freela[0])
    msg = f"E-mail enviado para {freela[0]}!" if success else "Erro ao enviar e-mail."
    return redirect(f"/buscar?mensagem={msg}")


@app.route("/excluir/<int:freelancer_id>")
def excluir(freelancer_id: int):
    if not is_logged_in():
        return redirect("/login")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # ON DELETE CASCADE handles avaliacoes automatically
            cur.execute("DELETE FROM freelancers WHERE id = %s", (freelancer_id,))
        conn.commit()

    return redirect("/buscar?mensagem=Freelancer removido com sucesso!")


@app.route("/avaliar/<int:freelancer_id>", methods=["GET", "POST"])
def avaliar(freelancer_id: int):
    if not is_logged_in():
        return redirect("/login")

    with get_conn() as conn:
        with conn.cursor() as cur:
            if request.method == "POST":
                nota = int(request.form["nota"])
                comentario = request.form["comentario"]

                cur.execute(
                    "DELETE FROM avaliacoes WHERE freelancer_id = %s", (freelancer_id,)
                )
                cur.execute(
                    "INSERT INTO avaliacoes (freelancer_id, nota, comentario) VALUES (%s, %s, %s)",
                    (freelancer_id, nota, comentario),
                )
                cur.execute(
                    "UPDATE freelancers SET score = %s WHERE id = %s",
                    (nota, freelancer_id),
                )
                conn.commit()

            cur.execute("SELECT * FROM freelancers WHERE id = %s", (freelancer_id,))
            freelancer = cur.fetchone()
            cur.execute(
                "SELECT COUNT(*) FROM avaliacoes WHERE freelancer_id = %s",
                (freelancer_id,),
            )
            total_avaliacoes = cur.fetchone()[0]

    sucesso = request.method == "POST"
    return render_template(
        "avaliacao.html",
        freelancer=freelancer,
        avaliacoes=total_avaliacoes,
        sucesso=sucesso,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)