import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from flask.json.provider import DefaultJSONProvider

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'planetun-monitoria-secret-key-2024')

DB_PATH = os.path.join(os.path.dirname(__file__), 'monitoria.db')

ITEMS = {
    1: {'numero': 1, 'categoria': 'GRAV\u00cdSSIMA', 'nome': 'Apontamentos Inadequados', 'descricao': 'Deixou de fazer os devidos apontamentos da an\u00e1lise do risco no laudo...'},
    2: {'numero': 2, 'categoria': 'GRAV\u00cdSSIMA', 'nome': 'Confer\u00eancia de Informa\u00e7\u00f5es e fotos do Ve\u00edculo', 'descricao': 'N\u00e3o conferiu os dados (modelo, placa e chassi)...'},
    3: {'numero': 3, 'categoria': 'GRAV\u00cdSSIMA', 'nome': 'Valida\u00e7\u00e3o de An\u00e1lise por IA', 'descricao': 'N\u00e3o realizou a confer\u00eancia dos apontamentos sugeridos pela IA...'},
    4: {'numero': 4, 'categoria': 'GRAVE', 'nome': 'Solicita\u00e7\u00e3o Indevida de Fotos', 'descricao': 'Solicitou corre\u00e7\u00f5es ou envio de fotos adicionais de maneira incorreta...'},
    5: {'numero': 5, 'categoria': 'GRAVE', 'nome': 'Or\u00e7amenta\u00e7\u00e3o Incorreta (aplic\u00e1vel a EA)', 'descricao': 'Realizou or\u00e7amento incorreto, desconsiderando imagens, pe\u00e7as...'},
    6: {'numero': 6, 'categoria': 'LEVE', 'nome': 'Preenchimento Incorreto de Dados', 'descricao': 'Erro no preenchimento das informa\u00e7\u00f5es da vistoria...'},
    7: {'numero': 7, 'categoria': 'LEVE', 'nome': 'Falta de Registro de Solicita\u00e7\u00e3o de Fotos e/ou observa\u00e7\u00f5es', 'descricao': 'N\u00e3o houve registro sobre solicita\u00e7\u00e3o de fotos adicionais...'},
    8: {'numero': 8, 'categoria': 'LEVE', 'nome': 'Relato de Avarias', 'descricao': 'N\u00e3o realizou o relato das avarias conforme as regras...'},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_usuario(usuario_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def calculate_score(marcados):
    score = 100
    if any(marcados.get(i, False) for i in [1, 2, 3]):
        return 0
    grave_count = sum(1 for i in [4, 5] if marcados.get(i, False))
    score -= grave_count * 60
    leve_count = sum(1 for i in [6, 7, 8] if marcados.get(i, False))
    score -= leve_count * 40
    return max(0, score)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ? AND ativo = 1', (email,))
        usuario = cursor.fetchone()
        conn.close()
        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_perfil'] = usuario['perfil']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', erro='Email ou senha inv\u00e1lidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/formulario', methods=['GET', 'POST'])
@login_required
def formulario():
    usuario = get_usuario(session['usuario_id'])
    if usuario['perfil'] != 'supervisor':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        colaborador_id = request.form.get('colaborador_id', type=int)
        cliente_id = request.form.get('cliente_id', type=int)
        data_monitoria = request.form.get('data_monitoria')
        data_tratativa = request.form.get('data_tratativa') or None
        data_feedback = request.form.get('data_feedback') or None
        numero_processo = request.form.get('numero_processo') or None
        observacoes = request.form.get('observacoes') or None
        marcados = {}
        for i in range(1, 9):
            marcados[i] = request.form.get(f'item_{i}') == 'on'
        nota_final = calculate_score(marcados)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO monitorias
            (data_monitoria, data_tratativa, data_feedback, colaborador_id, avaliador_id,
             cliente_id, numero_processo, observacoes, nota_final)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data_monitoria, data_tratativa, data_feedback, colaborador_id,
              session['usuario_id'], cliente_id, numero_processo, observacoes, nota_final))
        monitoria_id = cursor.lastrowid
        for item_numero, marcado in marcados.items():
            cursor.execute('''
                INSERT INTO monitoria_itens (monitoria_id, item_numero, marcado)
                VALUES (?, ?, ?)
            ''', (monitoria_id, item_numero, marcado))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome FROM usuarios WHERE perfil = "perito" AND ativo = 1 ORDER BY nome')
    peritos = cursor.fetchall()
    cursor.execute('SELECT id, nome FROM clientes ORDER BY nome')
    clientes = cursor.fetchall()
    conn.close()
    return render_template('formulario.html', items=ITEMS, peritos=peritos, clientes=clientes, avaliador_nome=usuario['nome'])

@app.route('/dashboard')
@login_required
def dashboard():
    usuario = get_usuario(session['usuario_id'])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome FROM usuarios WHERE perfil = "perito" AND ativo = 1 ORDER BY nome')
    peritos = cursor.fetchall()
    cursor.execute('SELECT id, nome FROM usuarios WHERE perfil = "supervisor" AND ativo = 1 ORDER BY nome')
    supervisores = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', usuario=usuario, peritos=peritos, supervisores=supervisores)

@app.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    usuario = get_usuario(session['usuario_id'])
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    perito_id = request.args.get('perito_id', type=int)
    supervisor_id = request.args.get('supervisor_id', type=int)
    conn = get_db()
    cursor = conn.cursor()
    query = '''
        SELECT m.*, u1.nome as colaborador_nome, u2.nome as avaliador_nome, c.nome as cliente_nome
        FROM monitorias m
        JOIN usuarios u1 ON m.colaborador_id = u1.id
        JOIN usuarios u2 ON m.avaliador_id = u2.id
        JOIN clientes c ON m.cliente_id = c.id
        WHERE 1=1
    '''
    params = []
    if usuario['perfil'] == 'perito':
        query += ' AND m.colaborador_id = ?'
        params.append(usuario['id'])
    elif perito_id:
        query += ' AND m.colaborador_id = ?'
        params.append(perito_id)
    if supervisor_id:
        query += ' AND m.avaliador_id = ?'
        params.append(supervisor_id)
    if mes and ano:
        query += ' AND strftime("%m", m.data_monitoria) = ? AND strftime("%Y", m.data_monitoria) = ?'
        params.extend([f'{mes:02d}', f'{ano:04d}'])
    query += ' ORDER BY m.data_monitoria DESC'
    cursor.execute(query, params)
    monitorias = cursor.fetchall()
    total_monitorias = len(monitorias)
    if total_monitorias > 0:
        nota_media = sum(m['nota_final'] for m in monitorias) / total_monitorias
        conformidade = sum(1 for m in monitorias if m['nota_final'] == 100) / total_monitorias * 100
        gravissima_count = 0
        for m in monitorias:
            cursor.execute('SELECT COUNT(*) as count FROM monitoria_itens WHERE monitoria_id = ? AND item_numero IN (1, 2, 3) AND marcado = 1', (m['id'],))
            gravissima_count += cursor.fetchone()['count']
        pct_gravissima = (gravissima_count / total_monitorias) * 100
    else:
        nota_media = 0
        conformidade = 0
        pct_gravissima = 0
    if usuario['perfil'] == 'perito':
        cursor.execute('SELECT u.nome, AVG(m.nota_final) as media_nota, COUNT(m.id) as total FROM monitorias m JOIN usuarios u ON m.colaborador_id = u.id WHERE u.perfil = \'perito\' AND m.colaborador_id = ?', (usuario['id'],))
    else:
        if perito_id:
            cursor.execute('SELECT u.nome, AVG(m.nota_final) as media_nota, COUNT(m.id) as total FROM monitorias m JOIN usuarios u ON m.colaborador_id = u.id WHERE u.perfil = \'perito\' AND m.colaborador_id = ?', (perito_id,))
        else:
            cursor.execute('SELECT u.nome, AVG(m.nota_final) as media_nota, COUNT(m.id) as total FROM monitorias m JOIN usuarios u ON m.colaborador_id = u.id WHERE u.perfil = \'perito\'')
    peritos_stats = cursor.fetchall()
    peritos_data = {'labels': [p['nome'] for p in peritos_stats], 'data': [round(p['media_nota'], 2) if p['media_nota'] else 0 for p in peritos_stats]}
    cursor.execute("SELECT strftime('%Y-%m', m.data_monitoria) as mes_ano, AVG(m.nota_final) as media FROM monitorias m WHERE m.data_monitoria >= date('now', '-12 months') GROUP BY strftime('%Y-%m', m.data_monitoria) ORDER BY mes_ano")
    monthly_stats = cursor.fetchall()
    monthly_data = {'labels': [m['mes_ano'] for m in monthly_stats], 'data': [round(m['media'], 2) if m['media'] else 0 for m in monthly_stats]}
    sem_falha = sum(1 for m in monitorias if m['nota_final'] == 100)
    leve = sum(1 for m in monitorias if m['nota_final'] in range(20, 100))
    grave = sum(1 for m in monitorias if m['nota_final'] in range(1, 20))
    gravissima = sum(1 for m in monitorias if m['nota_final'] == 0)
    failure_data = {'labels': ['Sem Falha', 'Falha Leve', 'Falha Grave', 'Falha Grav\u00edssima'], 'data': [sem_falha, leve, grave, gravissima]}
    ultimas_monitorias = [{'id': m['id'], 'data': m['data_monitoria'], 'perito': m['colaborador_nome'], 'supervisor': m['avaliador_nome'], 'cliente': m['cliente_nome'], 'nota': round(m['nota_final'], 2)} for m in monitorias[:10]]
    conn.close()
    return jsonify({'kpis': {'total_monitorias': total_monitorias, 'nota_media': round(nota_media, 2), 'pct_gravissima': round(pct_gravissima, 2), 'pct_conformidade': round(conformidade, 2)}, 'peritos': peritos_data, 'monthly': monthly_data, 'failures': failure_data, 'ultimas_monitorias': ultimas_monitorias})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
