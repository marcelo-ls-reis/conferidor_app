from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS jogos
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       numeros TEXT NOT NULL,
                       mes TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

def obter_resultados():
    url = "https://loteriascaixa-api.herokuapp.com/api/diadesorte/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def conferir_resultado(resultados, numeros_escolhidos, mes_escolhido):
    if not resultados:
        return "Não foi possível conferir o resultado."
    
    ultimo_concurso = resultados
    numeros_sorteados = [int(num) for num in ultimo_concurso['dezenas']]
    mes_sorte = ultimo_concurso['mesSorte']
    
    acertos = len(set(numeros_escolhidos) & set(numeros_sorteados))
    mes_acerto = mes_sorte.lower() == mes_escolhido.lower()
    
    return {
        "numeros_sorteados": numeros_sorteados,
        "mes_sorte": mes_sorte,
        "seus_numeros": numeros_escolhidos,
        "mes_escolhido": mes_escolhido,
        "acertos": acertos,
        "mes_acerto": mes_acerto
    }

@app.route('/') 
def index():
    conn = sqlite3.connect('database.db') 
    cursor = conn.cursor()
    cursor.execute("SELECT id, numeros, mes FROM jogos")
    jogos = cursor.fetchall()
    conn.close()
    return render_template('index.html', jogos=jogos)

@app.route('/add', methods=['POST'])
def add():
    numeros = request.form.get('numeros')
    mes = request.form.get('mes')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO jogos (numeros, mes) VALUES (?, ?)", (numeros, mes))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jogos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        numeros = request.form.get('numeros')
        mes = request.form.get('mes')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE jogos SET numeros = ?, mes = ? WHERE id = ?", (numeros, mes, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT numeros, mes FROM jogos WHERE id = ?", (id,))
        jogo = cursor.fetchone()
        conn.close()
        return render_template('edit.html', id=id, jogo=jogo)

@app.route('/resultados')
def resultados():
    resultados = obter_resultados()
    if resultados:
        numero_concurso = resultados.get('concurso')
        data_concurso = resultados.get('data')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT numeros, mes FROM jogos")
        jogos = cursor.fetchall()
        conn.close()

        resultados_finais = []
        for jogo in jogos:
            numeros_escolhidos = [int(num) for num in jogo[0].split(',')]
            mes_escolhido = jogo[1]
            resultado = conferir_resultado(resultados, numeros_escolhidos, mes_escolhido)
            resultados_finais.append(resultado)

        return render_template('results.html', resultados=resultados_finais, numero_concurso=numero_concurso, data_concurso=data_concurso)
    else:
        return "Não foi possível obter os resultados da loteria."


if __name__ == '__main__':
    app.run(debug=True)
