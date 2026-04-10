import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'monitoria.db')

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        perfil TEXT NOT NULL CHECK(perfil IN ('supervisor', 'perito')),
        ativo BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE monitorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_monitoria DATE NOT NULL,
        data_tratativa DATE,
        data_feedback DATE,
        colaborador_id INTEGER NOT NULL,
        avaliador_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        numero_processo TEXT,
        observacoes TEXT,
        nota_final FLOAT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (colaborador_id) REFERENCES usuarios(id),
        FOREIGN KEY (avaliador_id) REFERENCES usuarios(id),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE monitoria_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitoria_id INTEGER NOT NULL,
        item_numero INTEGER NOT NULL CHECK(item_numero >= 1 AND item_numero <= 8),
        marcado BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (monitoria_id) REFERENCES monitorias(id) ON DELETE CASCADE,
        UNIQUE(monitoria_id, item_numero)
    )
    ''')

    clientes = [
        'BANCO RODOBENS S.A.',
        'RODOBENS ADMINISTRADORA DE CONSORCIOS LTDA',
        'PORTOBENS ADMINISTRADORA DE CONSORCIOS LTDA',
        'BRQUALY ADMINISTRADORA DE CONSORCIOS LTDA',
        'CNF - ADMINISTRADORA DE CONSORCIOS NACIONAL LTDA',
        'MITSUI SUMITOMO SEGUROS',
        'SANCOR SEGUROS',
        'TOKIO MARINE BRASIL SEGURADORA S.A',
        'WIZ BPO SERVICOS DE TELEATENDIMENTO LTDA'
    ]

    for cliente in clientes:
        cursor.execute('INSERT INTO clientes (nome) VALUES (?)', (cliente,))

    password_hash = generate_password_hash('planetun123', method='pbkdf2:sha256')

    peritos = [
        'Abner Batista de Jesus', 'Anderson Henrique Roque de Lima', 'Anderson Soares',
        'Andre Luiz Souza Farias', 'Ari Santos', 'Carlos Henrique de Moura',
        'Cristiano Alves Pinto', 'Dalton Alexandre de Souza', 'Danilo Santos',
        'Diego Aguiar', 'Eduardo Vitor Bastos Silva', 'Eurico da Costa',
        'Jairo Luiz Junior', 'Jo\u00e3o Felipe Casagrande', 'Junio Viana',
        'Lucas Vinicius', 'Orlando Alberto', 'Paulo Marcio da Cruz Mota',
        'Pedro Jackson Ramos Eufrasio', 'Rodrigo Alexandre', 'Thiesare Vinicius',
        'Urival Souza dos Reis', 'Valentin Mediros Junior', 'Varley Henrique S R',
        'Zico Silva', 'Anderson Clayton Oliveira da Silva Clayton',
        'Diego Gon\u00e7alves Paranhos', 'Edilson Almada', 'Guilherme Nonato'
    ]

    for perito in peritos:
        email = perito.lower().replace(' ', '.') + '@planetun.com.br'
        cursor.execute(
            'INSERT INTO usuarios (nome, email, senha, perfil, ativo) VALUES (?, ?, ?, ?, ?)',
            (perito, email, password_hash, 'perito', 1)
        )

    supervisores = [
        'Filipi Schlichting Ramos', 'Andress Zangirolam', 'Anderson Barboza',
        'Cintia Carneiro', 'Josias Pereira'
    ]

    for supervisor in supervisores:
        email = supervisor.lower().replace(' ', '.') + '@planetun.com.br'
        cursor.execute(
            'INSERT INTO usuarios (nome, email, senha, perfil, ativo) VALUES (?, ?, ?, ?, ?)',
            (supervisor, email, password_hash, 'supervisor', 1)
        )

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {DB_PATH}")

if __name__ == '__main__':
    init_db()
