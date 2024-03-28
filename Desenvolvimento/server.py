from flask import Flask, render_template, jsonify, request, redirect, session, abort
from flask_session import Session
import json
import mysql.connector
from google_auth_oauthlib.flow import Flow
import os
import brazilcep



# Conexão com o banco de dados MYSQL
mydb = mysql.connector.connect(
      host='localhost',
      user='root',
      password='2077',
      database='iFood',
)


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = 'ifood-impacta'

# Variavel do banco global
my_cursor = mydb.cursor()

# Configuração Google
google_client_id = "1050537476605-dkp7bhag3qf1gohn21gl8rlahourrolc.apps.googleusercontent.com"
client_teste = os.path.join("C:\\Users\\ferre\\OneDrive\\Área de Trabalho\\iFood", "client_secret.json")
flow = Flow.from_client_secrets_file(client_secrets_file=client_teste,
scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
redirect_uri="https://127.0.0.1:5000/retorno")

def precisa_logar(function):
	def wrapper(*args, **kwargs):
		if "google_id" not in session:
			return abort(401) # precisa de permissão
		else:
			return function()
	return wrapper

def validarlogin(function):
    def validar(*args, **kwargs):
        if not session.get("user"):
            return redirect("/entrar")
        return function()
    return validar

def pegarnome():
	usuario  = session.get("user")
	global nome
	my_cursor.execute(f"SELECT nome FROM iFood.usuario WHERE user_id = {usuario}")
	nome = my_cursor.fetchall()[0][0]

def cad_endereco():
	usuario  = session.get("user")
	my_cursor.execute(f"UPDATE iFood.usuario SET endereco = '{retornar_endereco}' WHERE user_id = {usuario}")
	mydb.commit()

def cad_restaurante():
	usuario = session.get("user")
	my_cursor.execute(f"INSERT INTO iFood.restaurante (nome, endereco, telefone, owner, descricao) VALUES ('{restaurante}', '{endereco_restaurante}', '{telerestaurante}', {usuario}, '{descrestaurante}')")
	mydb.commit()

def carregar_restaurantes():
	global restaurantes
	my_cursor.execute("SELECT * FROM iFood.restaurante ")
	restaurantes = my_cursor.fetchall()

def buscar_restaurante():
	global valorbus
	coletar_busca = request.form.get("busca")
	my_cursor.execute(f"SELECT * FROM iFood.restaurante WHERE nome like '%{coletar_busca}%'")
	valorbus = my_cursor.fetchall()

def carregar_meus_restaurantes():
	usuario = session.get("user")
	global meus_restaurantes
	my_cursor.execute(f"SELECT id, nome, descricao FROM iFood.restaurante WHERE owner = {usuario}")
	meus_restaurantes = my_cursor.fetchall()

def verify():
    if not session.get("user"):
    	return redirect("/entrar")
	

# telas
@app.route("/")
def index():
	return render_template("index.html")

@app.route("/entrar")
def index_entrar():
	return render_template("login.html")
    
	  
@app.route("/cadastro")
def index_cadastrar():
	return render_template("cadastro.html")

@app.route("/cad_restaurante", methods=["GET", "POST"])
def index_restaurante():

	if request.method == "GET":
		return render_template("cadrestaurante.html")
	else:
		global restaurante
		global telerestaurante
		global descrestaurante
		restaurante = request.form.get("nomerestaurante")
		enderestaurante = request.form.get("enderecorestaurante") #tratar
		telerestaurante = request.form.get("telefonerestaurante")
		descrestaurante = request.form.get("descricaorestaurante")

		global endereco_restaurante
		address = brazilcep.get_address_from_cep(f'{enderestaurante}')
		endereco_restaurante = address['street']

		# print(restaurante, endereco_restaurante, telerestaurante)
		cad_restaurante()
		return redirect("/inicio")


@app.route("/inicio")
# @precisa_logar está chamando a função de logar
@validarlogin
def index_inicio():


	usuario  = session.get("user")
	my_cursor.execute(f"SELECT nome FROM iFood.usuario WHERE user_id = {usuario}")
	nome = my_cursor.fetchall()[0][0]
	
	carregar_restaurantes()

	return render_template("home.html", nome=nome, restaurantes=restaurantes)

	

@app.route("/buscando", methods=["POST"])
def buscar_res():
	buscar_restaurante()
	return redirect("/busca")

@app.route("/busca")
def busca_fin():
	pegarnome()
	return render_template("busca.html", valorbus=valorbus, nome=nome)


@app.route("/inicio/ende", methods=["POST"])
def carrecarcep():
    cep = request.form.get("busca")
    address = brazilcep.get_address_from_cep(f'{cep}')
    retorno = address['street']

    return render_template("home.html", end=retorno)

@app.route("/meus_dados", methods=['POST', 'GET'])
def mdados():
	if not session.get("user"):
		return redirect("/entrar")


	if request.method == 'GET':
		pegarnome()
		carregar_meus_restaurantes()
		usuario  = session.get("user")
		my_cursor.execute(f"SELECT endereco FROM iFood.usuario WHERE user_id = {usuario}")
		end_cadastrado= my_cursor.fetchall()[0][0]
		print(end_cadastrado)
		return render_template("mdados.html", nome=nome, end_cadastrado=end_cadastrado, meus_restaurantes=meus_restaurantes)


	else:
		global retornar_endereco
		coletarcep = request.form.get("cep")
		address = brazilcep.get_address_from_cep(f'{coletarcep}')
		retornar_endereco = address['street']
		cad_endereco()
		return redirect("/meus_dados")

@app.route("/retorno")
def retorno():
	a=flow.fetch_token(authorization_response=request.url)
	if not session["state"] == request.args["state"]:
		abort(500)
	return redirect('/inicio')
	
# funções para o banco de dados
# Cadastrar usuário
@app.route("/cadastrando", methods=['POST'])
def cadastrar():
	nome = request.form.get('nome')
	cpf = request.form.get('cpf')
	email = request.form.get('email')
	senha = request.form.get('senha')
	my_cursor.execute(f'INSERT INTO iFood.usuario (nome, cpf, email, senha) VALUES ("{nome}", "{cpf}", "{email}", sha1("{senha}"))')
	mydb.commit()
	mensagem_login = "Usuário cadastrado com sucesso!"
	
	return redirect("/entrar")

# Validar Login
@app.route("/entrando", methods=['POST'])
def entrar():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    my_cursor.execute(f'SELECT * FROM iFood.usuario where email = "{email}" AND senha = sha1("{senha}")')
    login = my_cursor.fetchall()
    # coletar id
    id = 0
    for i in login:
        id = i[0]
        print(id)
    
    if login == []:
        mensagem = "Usuário não encontrado"
        return render_template("login.html", mensagem=mensagem)
    else:
        session["user"] = id
        return redirect("/inicio")

	
		
    
	
# Retornar usuários cadastrados
@app.route("/usuarios")
def retornar_banco():
	my_cursor.execute("SELECT * FROM iFood.usuario")
	dados = my_cursor.fetchall()
	return dados

# Fazer o update do telefone do usuário 
@app.route('/update/<id>/<telefone>')
def update(id, telefone):
    my_cursor.execute(f"UPDATE  iFood.usuario SET telefone = '{telefone}' WHERE user_id = {id}")
    mydb.commit()
    return "Update realizado com sucesso."

# Deletar conta de usuário
@app.route('/delete/<id>')
def deletar(id):
    my_cursor.execute(f"delete from iFood.usuario where user_id = {id}")
    mydb.commit()
    return "Delete realizado com sucesso."

# LOGIN GOOGLE -------------------- Importante
@app.route("/logando_google")
def logar_google():

	authorization_url, state = flow.authorization_url()
	session["state"] = state
	teste = session.get("state")
	return f"{teste}"
	# return redirect(authorization_url)


# Fechar sessão -------------------- Importante
@app.route("/sair")
def sair():
	session.clear()
	return redirect("/")

if __name__ == "__main__":
	app.run(debug=True)
	
