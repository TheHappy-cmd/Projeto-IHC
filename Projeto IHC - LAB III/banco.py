import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

CAMINHO = Path(__file__).with_name("studyup.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS areas (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS mentores (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL,
    profissao TEXT NOT NULL,
    foto      TEXT,
    area_id   INTEGER NOT NULL REFERENCES areas(id)
);

CREATE TABLE IF NOT EXISTS vagas (
    id         INTEGER PRIMARY KEY,
    titulo     TEXT NOT NULL,
    area_id    INTEGER NOT NULL REFERENCES areas(id),
    modalidade TEXT NOT NULL,
    local      TEXT NOT NULL,
    descricao  TEXT NOT NULL,
    link       TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    curso      TEXT,
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidaturas (
    id         INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    vaga_id    INTEGER NOT NULL REFERENCES vagas(id),
    status     TEXT NOT NULL DEFAULT 'enviada',
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_id, vaga_id)
);

CREATE TABLE IF NOT EXISTS mentorias (
    id         INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    mentor_id  INTEGER NOT NULL REFERENCES mentores(id),
    mensagem   TEXT,
    status     TEXT NOT NULL DEFAULT 'pendente',
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_id, mentor_id)
);
"""

LINK = "https://docs.google.com/forms/d/e/1FAIpQLSdlfEIOhSxA9qEKjRyr7GLQ93oLHKOa8ITt6DkHw6OkXezInw/viewform?usp=publish-editor"

AREAS = [
    (1, "Tecnologia"),
    (2, "Mecânica Automotiva"),
    (3, "Direito"),
    (4, "Saúde"),
    (5, "Agricultura"),
    (6, "Educação"),
]

MENTORES = [
    ("Luiz Bulhões", "Advogado", "advogado.jpg", 3),
    ("Marcos Paixão", "Enfermeiro", "enfermeiro.jpg", 4),
    ("Laelson Barbosa", "Engenheiro de Software", "engenheiro.jpg", 1),
    ("Cezar Batista", "Agricultor", "agricultor.jpg", 5),
    ("Glauco Ferreira", "Mecânico", "mecanico.jpg", 2),
    ("Leyla Medeiros", "Professora de Língua portuguesa", "professora.jpg", 6),
]

VAGAS = [
    ("Estágio em Cibersegurança", 1, "Híbrido", "Maceió - AL",
     "Oportunidade para estudantes que desejam aprender sobre segurança de sistemas e redes.", LINK),
    ("Auxiliar de Mecânico", 2, "Presencial", "Maceió - AL",
     "Oportunidade para aprender e auxiliar na manutenção, revisão e reparação de veículos.", LINK),
    ("Estágio em Direito", 3, "Presencial", "Maceió - AL",
     "Oportunidade para estudantes de Direito acompanharem processos, pesquisas jurídicas e atividades de um escritório.", LINK),
    ("Estágio em Enfermagem", 4, "Presencial", "Maceió - AL",
     "Oportunidade para estudantes desenvolverem conhecimentos práticos e acompanharem profissionais da área da saúde.", LINK),
]


def conectar():
    con = sqlite3.connect(CAMINHO)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def criar_banco():
    con = conectar()
    con.executescript(ESQUEMA)
    if con.execute("SELECT COUNT(*) FROM areas").fetchone()[0] == 0:
        con.executemany("INSERT INTO areas (id, nome) VALUES (?, ?)", AREAS)
        con.executemany(
            "INSERT INTO mentores (nome, profissao, foto, area_id) VALUES (?, ?, ?, ?)", MENTORES
        )
        con.executemany(
            "INSERT INTO vagas (titulo, area_id, modalidade, local, descricao, link) VALUES (?, ?, ?, ?, ?, ?)",
            VAGAS,
        )
    con.commit()
    con.close()


def listar_mentores():
    con = conectar()
    linhas = con.execute(
        "SELECT m.id, m.nome, m.profissao, m.foto, a.nome AS area "
        "FROM mentores m JOIN areas a ON a.id = m.area_id ORDER BY m.id"
    ).fetchall()
    con.close()
    return [dict(l) for l in linhas]


def listar_vagas():
    con = conectar()
    linhas = con.execute(
        "SELECT v.id, v.titulo, a.nome AS area, v.modalidade, v.local, v.descricao, v.link "
        "FROM vagas v JOIN areas a ON a.id = v.area_id ORDER BY v.id"
    ).fetchall()
    con.close()
    return [dict(l) for l in linhas]


def cadastrar_usuario(nome, email, senha, curso):
    con = conectar()
    try:
        cur = con.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, curso) VALUES (?, ?, ?, ?)",
            (nome.strip(), email.strip().lower(), generate_password_hash(senha), curso),
        )
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        con.close()


def autenticar(email, senha):
    con = conectar()
    linha = con.execute(
        "SELECT id, nome, senha_hash FROM usuarios WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    con.close()
    if linha and check_password_hash(linha["senha_hash"], senha):
        return {"id": linha["id"], "nome": linha["nome"]}
    return None


def candidatar(usuario_id, vaga_id):
    con = conectar()
    try:
        con.execute("INSERT INTO candidaturas (usuario_id, vaga_id) VALUES (?, ?)", (usuario_id, vaga_id))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


def solicitar_mentoria(usuario_id, mentor_id, mensagem=None):
    con = conectar()
    try:
        con.execute(
            "INSERT INTO mentorias (usuario_id, mentor_id, mensagem) VALUES (?, ?, ?)",
            (usuario_id, mentor_id, mensagem),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


def listar_candidaturas():
    con = conectar()
    linhas = con.execute(
        "SELECT u.nome, u.email, v.titulo, c.status, c.criado_em "
        "FROM candidaturas c JOIN usuarios u ON u.id = c.usuario_id "
        "JOIN vagas v ON v.id = c.vaga_id ORDER BY c.id"
    ).fetchall()
    con.close()
    return [dict(l) for l in linhas]


def listar_mentorias():
    con = conectar()
    linhas = con.execute(
        "SELECT u.nome, u.email, m.nome AS mentor, t.mensagem, t.status, t.criado_em "
        "FROM mentorias t JOIN usuarios u ON u.id = t.usuario_id "
        "JOIN mentores m ON m.id = t.mentor_id ORDER BY t.id"
    ).fetchall()
    con.close()
    return [dict(l) for l in linhas]


if __name__ == "__main__":
    criar_banco()
    print("Banco criado:", CAMINHO)
    print("Mentores:", len(listar_mentores()))
    print("Vagas:", len(listar_vagas()))
