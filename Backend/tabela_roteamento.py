from flask import Flask, request, jsonify
import socket
app = Flask(__name__)

ip = socket.gethostbyname(socket.gethostname())

# Dicionário para a tabela de roteamento
tabela_roteamento = {}

# Carregar tabela de roteamento
def carregar_tabela_roteamento():
    return tabela_roteamento

# Atualizar tabela de roteamento
def atualizar_tabela_roteamento(banco_id, url):
    tabela_roteamento[banco_id] = url

@app.route('/get_banks', methods=['GET'])
def get_tabela_roteamento():
    return jsonify(carregar_tabela_roteamento()), 200

@app.route('/put_banks', methods=['PUT'])
def put_tabela_roteamento():
    dados = request.json
    banco_id = dados.get('banco_id')
    url = dados.get('url')
    if not banco_id or not url:
        return jsonify({'erro': 'Dados inválidos'}), 400

    atualizar_tabela_roteamento(banco_id, url)
    print(tabela_roteamento)
    return jsonify({'mensagem': 'Tabela de roteamento atualizada com sucesso'}), 200

if __name__ == '__main__':
    app.run(host=ip, port=4326, debug=True)
