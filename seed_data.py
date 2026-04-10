import sqlite3
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'monitoria.db')

def add_user_if_not_exists(cursor, nome, email, senha, perfil):
    cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
    if cursor.fetchone():
        print(f"  {email} j\u00e1 existe.")
        return
    password_hash = generate_password_hash(senha, method='pbkdf2:sha256')
    cursor.execute(
        'INSERT INTO usuarios (nome, email, senha, perfil, ativo) VALUES (?, ?, ?, ?, ?)',
        (nome, email, password_hash, perfil, 1)
    )
    print(f"  {email} ({perfil}) criado.")

def calculate_score(marcados):
    score = 100
    if any(marcados.get(i, False) for i in [1, 2, 3]):
        return 0
    for i in [4, 5]:
        if marcados.get(i, False):
            score -= 60
    for i in [6, 7, 8]:
        if marcados.get(i, False):
            score -= 40
    return max(0, score)

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("\n=== Adicionando usu\u00e1rios ===")
    add_user_if_not_exists(cursor, 'Diego Zago', 'diego@planetun.com.br', 'planetun123', 'supervisor')
    add_user_if_not_exists(cursor, 'Natalia', 'natalia@planetun.com.br', 'planetun123', 'supervisor')
    conn.commit()
    cursor.execute("SELECT id FROM usuarios WHERE perfil = 'supervisor'")
    supervisor_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM usuarios WHERE perfil = 'perito'")
    perito_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM clientes")
    cliente_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("DELETE FROM monitoria_itens")
    cursor.execute("DELETE FROM monitorias")
    conn.commit()
    print("\n=== Gerando monitorias fict\u00edcias ===")
    hoje = datetime.now()
    num_monitorias = 120
    prob_falha = {1: 0.05, 2: 0.04, 3: 0.03, 4: 0.08, 5: 0.06, 6: 0.15, 7: 0.12, 8: 0.10}
    processo_base = 7400000
    count_by_month = {}
    for i in range(num_monitorias):
        dias_atras = random.randint(0, 180)
        data_monitoria = hoje - timedelta(days=dias_atras)
        data_tratativa = data_monitoria - timedelta(days=random.randint(0, 3))
        data_feedback = data_monitoria + timedelta(days=random.randint(1, 7)) if random.random() > 0.3 else None
        mes_key = data_monitoria.strftime('%Y-%m')
        count_by_month[mes_key] = count_by_month.get(mes_key, 0) + 1
        perito_id = random.choice(perito_ids)
        supervisor_id = random.choice(supervisor_ids)
        cliente_id = random.choice(cliente_ids)
        numero_processo = str(processo_base + random.randint(1, 99999))
        marcados = {}
        for item_num, prob in prob_falha.items():
            if random.random() < prob:
                marcados[item_num] = True
        nota_final = calculate_score(marcados)
        observacoes = ""
        if nota_final == 0:
            observacoes = random.choice(["Falha cr\u00edtica identificada. Necess\u00e1rio retreinamento.", "Impacto operacional significativo. Agendar feedback urgente.", "Erro grave na an\u00e1lise. Revisar processo com o perito."])
        elif nota_final < 100:
            observacoes = random.choice(["Pequenos ajustes necess\u00e1rios no procedimento.", "Aten\u00e7\u00e3o ao preenchimento dos dados.", "Melhorar registro de solicita\u00e7\u00f5es.", "Verificar procedimento de relato de avarias.", "Orientar sobre padr\u00e3o de fotos adicionais."])
        cursor.execute('''
            INSERT INTO monitorias (data_monitoria, data_tratativa, data_feedback,
                colaborador_id, avaliador_id, cliente_id, numero_processo,
                observacoes, nota_final, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data_monitoria.strftime('%Y-%m-%d'), data_tratativa.strftime('%Y-%m-%d'),
            data_feedback.strftime('%Y-%m-%d') if data_feedback else None,
            perito_id, supervisor_id, cliente_id, numero_processo,
            observacoes, nota_final, data_monitoria.strftime('%Y-%m-%d %H:%M:%S')))
        monitoria_id = cursor.lastrowid
        for item_num in range(1, 9):
            cursor.execute('INSERT INTO monitoria_itens (monitoria_id, item_numero, marcado) VALUES (?, ?, ?)',
                (monitoria_id, item_num, marcados.get(item_num, False)))
    conn.commit()
    print(f"\n=== Resumo ===")
    print(f"  Total de monitorias geradas: {num_monitorias}")
    for mes in sorted(count_by_month.keys()):
        print(f"  {mes}: {count_by_month[mes]} monitorias")
    cursor.execute("SELECT AVG(nota_final) FROM monitorias")
    media = cursor.fetchone()[0]
    print(f"  Nota m\u00e9dia geral: {media:.1f}")
    cursor.execute("SELECT COUNT(*) FROM monitorias WHERE nota_final = 100")
    conformes = cursor.fetchone()[0]
    print(f"  Conformidade (nota 100): {conformes}/{num_monitorias} ({conformes/num_monitorias*100:.1f}%)")
    cursor.execute("SELECT COUNT(*) FROM monitorias WHERE nota_final = 0")
    gravissimas = cursor.fetchone()[0]
    print(f"  Falhas grav\u00edssimas (nota 0): {gravissimas}/{num_monitorias} ({gravissimas/num_monitorias*100:.1f}%)")
    conn.close()
    print("\nDados de demonstra\u00e7\u00e3o gerados com sucesso!")

if __name__ == '__main__':
    seed()
