"""
Renderiza as telas via Flask test client com dados fake e salva HTML estático
em preview_*.html — apenas para visualização rápida das mudanças.
"""
import os
import sqlite3
import sys
import tempfile

# Banco de teste isolado
TMP_DB = os.path.join(tempfile.gettempdir(), 'monitoria_preview.db')
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)
os.environ['DB_PATH'] = TMP_DB

# Cria schema mínimo + dados fake
conn = sqlite3.connect(TMP_DB)
c = conn.cursor()
c.executescript('''
CREATE TABLE usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  senha_hash TEXT NOT NULL,
  perfil TEXT NOT NULL,
  ativo BOOLEAN DEFAULT 1
);
CREATE TABLE clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE
);
CREATE TABLE produtos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE,
  ativo BOOLEAN NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE monitorias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_monitoria DATE NOT NULL,
  data_tratativa DATE,
  data_feedback DATE,
  colaborador_id INTEGER NOT NULL,
  avaliador_id INTEGER NOT NULL,
  cliente_id INTEGER NOT NULL,
  produto_id INTEGER,
  numero_processo TEXT,
  observacoes TEXT,
  nota_final FLOAT DEFAULT 0
);
CREATE TABLE monitoria_itens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  monitoria_id INTEGER NOT NULL,
  item_numero INTEGER NOT NULL,
  marcado BOOLEAN NOT NULL DEFAULT 0,
  observacao TEXT
);
CREATE TABLE monitoria_anexos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  monitoria_id INTEGER NOT NULL,
  item_numero INTEGER NOT NULL,
  nome_original TEXT NOT NULL,
  nome_arquivo TEXT NOT NULL,
  tamanho INTEGER,
  mime_type TEXT,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE monitoria_replicas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  monitoria_id INTEGER NOT NULL,
  autor_id INTEGER NOT NULL,
  autor_tipo TEXT NOT NULL,
  decisao TEXT NOT NULL,
  justificativa TEXT,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(monitoria_id, autor_tipo)
);

INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES
 ('Henrique Mazieiro', 'henrique@planetun.com.br', 'x', 'supervisor'),
 ('Carlos Pereira', 'carlos@planetun.com.br', 'x', 'perito'),
 ('João Silva', 'joao@planetun.com.br', 'x', 'perito'),
 ('Ana Souza', 'ana@planetun.com.br', 'x', 'perito');

INSERT INTO clientes (nome) VALUES ('Porto Seguro'), ('Itau Seguros'), ('Bradesco Auto');

INSERT INTO produtos (nome, ativo) VALUES
 ('Vistoria Prévia', 1),
 ('Vistoria de Sinistro', 1),
 ('Inspeção EA', 1),
 ('Roubo / Furto', 1),
 ('Inspeção de Frota', 0);
''')
# Cria 12 monitorias fake só pra mostrar uso
for i in range(12):
    c.execute(
        'INSERT INTO monitorias (data_monitoria, colaborador_id, avaliador_id, cliente_id, produto_id, nota_final) VALUES (?, ?, ?, ?, ?, ?)',
        ('2026-04-15', 2 + (i % 3), 1, 1 + (i % 3), 1 + (i % 4), 100 - (i * 5) % 60)
    )
# Adiciona uma monitoria com itens marcados + observações + anexos para o preview do detalhe
c.execute('''INSERT INTO monitorias
    (id, data_monitoria, data_tratativa, data_feedback, colaborador_id, avaliador_id,
     cliente_id, produto_id, numero_processo, observacoes, nota_final)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (999, '2026-04-25', '2026-04-26', None, 2, 1, 1, 1, '2026-04-00342',
     'Avaliação geral abaixo do esperado. Pontos críticos discutidos com o perito em call 26/04.', 0))
itens_marcados = {1: True, 2: False, 3: False, 4: True, 5: False, 6: False, 7: True, 8: False}
obs_por_item = {
    1: 'Perito não realizou apontamentos completos da análise de risco. Falta de validação visível no laudo.',
    4: 'Solicitou fotos adicionais ao cliente fora do protocolo padrão de comunicação.',
    7: 'Não houve registro formal da solicitação de fotos no sistema.',
}
for n, m in itens_marcados.items():
    c.execute('INSERT INTO monitoria_itens (monitoria_id, item_numero, marcado, observacao) VALUES (?, ?, ?, ?)',
              (999, n, m, obs_por_item.get(n) if m else None))
# Anexos fake (apenas registros — arquivos não existem)
c.execute('INSERT INTO monitoria_anexos (monitoria_id, item_numero, nome_original, nome_arquivo, tamanho, mime_type) VALUES (?, ?, ?, ?, ?, ?)',
          (999, 1, 'laudo_processo_342.pdf', 'item1_a1b2_laudo_processo_342.pdf', 2458921, 'application/pdf'))
c.execute('INSERT INTO monitoria_anexos (monitoria_id, item_numero, nome_original, nome_arquivo, tamanho, mime_type) VALUES (?, ?, ?, ?, ?, ?)',
          (999, 1, 'foto_chassi.jpg', 'item1_c3d4_foto_chassi.jpg', 184320, 'image/jpeg'))
c.execute('INSERT INTO monitoria_anexos (monitoria_id, item_numero, nome_original, nome_arquivo, tamanho, mime_type) VALUES (?, ?, ?, ?, ?, ?)',
          (999, 4, 'transcricao_call.docx', 'item4_e5f6_transcricao_call.docx', 45678, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))

# Cenário B: monitoria 998 com réplica do perito já enviada
c.execute('''INSERT INTO monitorias
    (id, data_monitoria, colaborador_id, avaliador_id, cliente_id, produto_id,
     numero_processo, observacoes, nota_final)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (998, '2026-04-22', 3, 1, 2, 2, '2026-04-00298',
     'Atraso na entrega do laudo final.', 60))
for n, m in {1: False, 2: False, 3: False, 4: False, 5: False, 6: True, 7: False, 8: False}.items():
    c.execute('INSERT INTO monitoria_itens (monitoria_id, item_numero, marcado, observacao) VALUES (?, ?, ?, ?)',
              (998, n, m, 'Laudo entregue com 18h de atraso após o prazo combinado.' if (m and n == 6) else None))
c.execute('INSERT INTO monitoria_replicas (monitoria_id, autor_id, autor_tipo, decisao, justificativa, criado_em) VALUES (?, ?, ?, ?, ?, ?)',
          (998, 3, 'perito', 'nao_concordo',
           'O atraso foi devido a um problema de acesso ao sistema da seguradora, que durou cerca de 12 horas no dia 22/04. Tenho prints e e-mails que comprovam. As outras 6h foram usadas para refazer fotos do veículo que vieram com qualidade ruim do app — fluxo que está fora do meu controle.',
           '2026-04-23 14:32:00'))

# Cenário C: monitoria 997 com réplica do perito + resposta do supervisor
c.execute('''INSERT INTO monitorias
    (id, data_monitoria, colaborador_id, avaliador_id, cliente_id, produto_id,
     numero_processo, observacoes, nota_final)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (997, '2026-04-18', 4, 1, 1, 1, '2026-04-00256',
     'Comunicação informal e fotos fora do padrão.', 20))
for n, m in {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: True, 8: True}.items():
    c.execute('INSERT INTO monitoria_itens (monitoria_id, item_numero, marcado, observacao) VALUES (?, ?, ?, ?)',
              (997, n, m, 'Falta de registro formal das solicitações.' if (m and n == 7) else ('Fotos fora do padrão visual exigido.' if (m and n == 8) else None)))
c.execute('INSERT INTO monitoria_replicas (monitoria_id, autor_id, autor_tipo, decisao, justificativa, criado_em) VALUES (?, ?, ?, ?, ?, ?)',
          (997, 4, 'perito', 'nao_concordo',
           'Discordo do item 7. Eu registrei as solicitações via WhatsApp do cliente porque foi o canal pedido por ele.',
           '2026-04-19 09:15:00'))
c.execute('INSERT INTO monitoria_replicas (monitoria_id, autor_id, autor_tipo, decisao, justificativa, criado_em) VALUES (?, ?, ?, ?, ?, ?)',
          (997, 1, 'supervisor', 'concordo',
           'Acolhida. Vou ajustar a avaliação do item 7 considerando o registro via WhatsApp como válido neste caso. Item 8 (fotos) permanece — vamos alinhar no próximo 1:1.',
           '2026-04-19 16:40:00'))

conn.commit()
conn.close()

# Aponta DB_PATH para o tmp ANTES de importar app
import app as flask_app  # noqa: E402
flask_app.DB_PATH = TMP_DB

OUT = '/sessions/beautiful-quirky-hamilton/mnt/Monitoria da Qualidade'

def render(route, filename, login_as=1, perfil='supervisor', nome='Henrique Mazieiro'):
    client = flask_app.app.test_client()
    with client.session_transaction() as sess:
        sess['usuario_id'] = login_as
        sess['usuario_nome'] = nome
        sess['usuario_perfil'] = perfil
    resp = client.get(route)
    print(f'{route}: {resp.status_code}')
    if resp.status_code == 200:
        path = os.path.join(OUT, filename)
        # Reescreve referências /static/ e /produtos para virar previews navegáveis
        html = resp.get_data(as_text=True)
        with open(path, 'w') as f:
            f.write(html)
        print(f'  -> {path}')
    else:
        print(f'  body: {resp.get_data(as_text=True)[:200]}')

render('/produtos', 'preview_produtos.html')
render('/formulario', 'preview_formulario.html')
render('/dashboard', 'preview_dashboard.html')
render('/historico', 'preview_historico.html')
render('/peritos', 'preview_peritos.html')

# Cenário A — Perito recebeu monitoria, ainda não respondeu (vê botões Concordo/Não)
render('/monitoria/999', 'preview_detalhe_A_perito_responder.html',
       login_as=2, perfil='perito', nome='Carlos Pereira')

# Cenário B — Perito já enviou réplica de "Não concordo", aguardando supervisor
render('/monitoria/998', 'preview_detalhe_B_perito_aguardando.html',
       login_as=3, perfil='perito', nome='João Silva')

# Cenário B-sup — Supervisor vê a réplica do perito e tem o formulário de resposta
render('/monitoria/998', 'preview_detalhe_B_supervisor_responder.html',
       login_as=1, perfil='supervisor', nome='Henrique Mazieiro')

# Cenário C — Ciclo completo: perito + supervisor já replicaram
render('/monitoria/997', 'preview_detalhe_C_ciclo_completo.html',
       login_as=4, perfil='perito', nome='Ana Souza')
