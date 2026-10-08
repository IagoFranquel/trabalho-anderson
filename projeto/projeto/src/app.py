import os

import psycopg2
import psycopg2.extras
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

DB = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "loja_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres"),
    client_encoding="UTF8",
)
# Se DATABASE_URL estiver definida (ex.: Supabase), ela tem prioridade.
DATABASE_URL = os.getenv("DATABASE_URL")


# ---------------------------------------------------------------- helpers
def connect():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, client_encoding="UTF8")
    return psycopg2.connect(**DB)


def run(sql, params=(), fetch="all"):
    """Executa uma instrução; faz commit e devolve linhas como dicionários."""
    conn = connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch == "all":
                    return cur.fetchall()
                if fetch == "one":
                    return cur.fetchone()
                return None
    finally:
        conn.close()


def erro_banco(e):
    """Mensagem amigável vinda do RAISE EXCEPTION do PostgreSQL."""
    diag = getattr(e, "diag", None)
    return (diag.message_primary if diag and diag.message_primary else str(e))


@app.template_filter("brl")
def brl(valor):
    valor = float(valor or 0)
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ rotas
@app.route("/")
def index():
    return redirect(url_for("relatorio_vendas"))


# TELA 1 - Relatório de Vendas  -> usa a VIEW vw_relatorio_vendas
@app.route("/vendas")
def relatorio_vendas():
    vendas = run("SELECT * FROM vw_relatorio_vendas ORDER BY data_venda DESC, venda_id DESC")
    ativas = [v for v in vendas if v["status"] == "CONCLUIDA"]
    resumo = {
        "qtd": len(ativas),
        "faturamento": sum(v["total"] for v in ativas),
        "descontos": sum(v["desconto"] for v in ativas),
    }
    return render_template("relatorio_vendas.html", vendas=vendas, resumo=resumo)


# TELA 2 - Nova Venda -> chama a PROCEDURE sp_realizar_venda
@app.route("/vendas/nova", methods=["GET", "POST"])
def nova_venda():
    if request.method == "POST":
        try:
            cliente_id = int(request.form["cliente_id"])
        except (KeyError, ValueError):
            flash("Selecione um cliente.", "erro")
            return redirect(url_for("nova_venda"))

        ids, qtds = [], []
        for chave, valor in request.form.items():
            if chave.startswith("produto_") and valor.strip().isdigit() and int(valor) > 0:
                ids.append(int(chave.split("_", 1)[1]))
                qtds.append(int(valor))

        if not ids:
            flash("Informe a quantidade de pelo menos um produto.", "erro")
            return redirect(url_for("nova_venda"))

        try:
            row = run(
                "CALL sp_realizar_venda(%s, %s::int[], %s::int[], NULL::int)",
                (cliente_id, ids, qtds),
                fetch="one",
            )
            flash(f"Venda #{row['p_venda_id']} registrada com sucesso!", "ok")
            return redirect(url_for("relatorio_vendas"))
        except psycopg2.Error as e:
            flash(erro_banco(e), "erro")
            return redirect(url_for("nova_venda"))

    clientes = run("SELECT id, nome, categoria FROM clientes ORDER BY nome")
    produtos = run("SELECT produto_id AS id, nome, preco, estoque FROM vw_estoque_situacao ORDER BY nome")
    return render_template("nova_venda.html", clientes=clientes, produtos=produtos)


# API usada pela tela Nova Venda -> chama a FUNCTION fn_calcular_desconto
@app.route("/api/desconto")
def api_desconto():
    try:
        cliente_id = int(request.args["cliente_id"])
        subtotal = float(request.args["subtotal"])
        row = run("SELECT fn_calcular_desconto(%s, %s) AS desconto", (cliente_id, subtotal), fetch="one")
        desconto = float(row["desconto"])
        return jsonify(desconto=desconto, total=round(subtotal - desconto, 2))
    except (KeyError, ValueError):
        return jsonify(erro="parâmetros inválidos"), 400
    except psycopg2.Error as e:
        return jsonify(erro=erro_banco(e)), 400


# Cancelamento -> chama a PROCEDURE sp_cancelar_venda
@app.route("/vendas/<int:venda_id>/cancelar", methods=["POST"])
def cancelar_venda(venda_id):
    try:
        run("CALL sp_cancelar_venda(%s)", (venda_id,), fetch=None)
        flash(f"Venda #{venda_id} cancelada e estoque devolvido.", "ok")
    except psycopg2.Error as e:
        flash(erro_banco(e), "erro")
    return redirect(url_for("relatorio_vendas"))


# TELA 3 - Estoque -> usa a VIEW vw_estoque_situacao
@app.route("/estoque")
def estoque():
    itens = run("SELECT * FROM vw_estoque_situacao ORDER BY situacao DESC, nome")
    return render_template("estoque.html", itens=itens)


# CRUD básico (evolução do trabalho anterior)
@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        try:
            run(
                "INSERT INTO clientes (nome, email, categoria) VALUES (%s, %s, %s)",
                (request.form["nome"].strip(), request.form["email"].strip() or None, request.form["categoria"]),
                fetch=None,
            )
            flash("Cliente cadastrado.", "ok")
        except psycopg2.Error as e:
            flash(erro_banco(e), "erro")
        return redirect(url_for("clientes"))
    lista = run("SELECT * FROM clientes ORDER BY nome")
    return render_template("clientes.html", clientes=lista)


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if request.method == "POST":
        try:
            run(
                "INSERT INTO produtos (nome, preco, estoque, estoque_minimo) VALUES (%s, %s, %s, %s)",
                (
                    request.form["nome"].strip(),
                    request.form["preco"],
                    request.form["estoque"],
                    request.form["estoque_minimo"],
                ),
                fetch=None,
            )
            flash("Produto cadastrado.", "ok")
        except psycopg2.Error as e:
            flash(erro_banco(e), "erro")
        return redirect(url_for("produtos"))
    lista = run("SELECT * FROM produtos ORDER BY nome")
    return render_template("produtos.html", produtos=lista)


if __name__ == "__main__":
    app.run(debug=True)
