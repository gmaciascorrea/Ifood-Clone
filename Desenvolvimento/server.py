from flask import Flask, render_template, jsonify, request, redirect, session, abort
from flask_session import Session
import json
import mysql.connector
from google_auth_oauthlib.flow import Flow
import os
import brazilcep
import time



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
	print("-------------------LOG COLETAR USUÁRIO-------------------------")
	print(f"Nome: {nome}")
	print("------------------------------------------------------------")

def cad_endereco():
	usuario  = session.get("user")
	# my_cursor.execute(f"UPDATE iFood.usuario SET endereco = '{retornar_endereco}' WHERE user_id = {usuario}")
	my_cursor.execute(f"INSERT INTO ifood.endereco (id_cliente, cep, Numero) VALUES ({usuario}, '{retornar_endereco}', '{numerocep}')")
	mydb.commit()

def cad_restaurante():
	usuario = session.get("user")
	my_cursor.execute(f"INSERT INTO iFood.restaurante (nome, endereco, telefone, owner, descricao) VALUES ('{restaurante}', '{endereco_restaurante}', '{telerestaurante}', {usuario}, '{descrestaurante}')")
	mydb.commit()

def carregar_restaurantes():
	global restaurantes
	my_cursor.execute("SELECT * FROM iFood.restaurante ")
	restaurantes = my_cursor.fetchall()

def carregar_cesta():
	global vcesta
	global vcesta_formatado
	global cesta_completa
	global restaurante_da_cesta
	usuario = session.get("user")
	my_cursor.execute(f"SELECT * FROM ifood.cesta WHERE id_cliente = {usuario}")
	cesta_completa = my_cursor.fetchall()
	vcesta= 0.00
	somar = 0.00


	print("-------------------LOG CESTA-------------------------")
	print(f"Cesta: {cesta_completa}") # ID da cesta // ID do cliente // Valor do item // ID do item // ID do restaurante
	print("-----------------------------------------------------")
	

	if cesta_completa == []:
		vcesta = 0.00
		vcesta_formatado = 0.00
	else:
		my_cursor.execute(f"SELECT * FROM ifood.cesta WHERE id_cliente = {usuario}")
		restaurante_da_cesta = my_cursor.fetchall()[0][4]
		for i in cesta_completa:
			restaurante_da_cesta = i[4]
			somar += float(i[2])
			vcesta = round(somar, 3)
			vcesta_formatado = "{:.2f}".format(vcesta)
			# print(f"o id do restaurante é {restaurante_da_cesta}")

def buscar_restaurante():
	global valorbus
	coletar_busca = request.form.get("busca")
	my_cursor.execute(f"SELECT * FROM iFood.restaurante WHERE nome like '%{coletar_busca}%'")
	valorbus = my_cursor.fetchall()
	print("-------------------RESTAURANTES PESQUISADOS-------------------------")
	print(f"Encontrado: {valorbus}")
	print("--------------------------------------------------------------------")

def carregar_meus_restaurantes():
	usuario = session.get("user")
	global meus_restaurantes
	my_cursor.execute(f"SELECT id, nome, descricao FROM iFood.restaurante WHERE owner = {usuario}")
	meus_restaurantes = my_cursor.fetchall()
	print("-------------------RESTAURANTES DO USUÁRIO-------------------------")
	print(f"Restaurantes: {meus_restaurantes}")
	print("-------------------------------------------------------------------")

def gerar_pedido_banco():
	carregar_cesta()
	
	usuario = session.get("user")
	my_cursor.execute(f"INSERT INTO iFood.pedido (user_id, store_id, data, valor) VALUES ({usuario}, {restaurante_da_cesta}, now(), {vcesta_formatado}) ")
	mydb.commit()
	my_cursor.execute("SELECT LAST_INSERT_ID()")
	global ultimo_pedido
	ultimo_pedido = my_cursor.fetchall()[0][0]
	my_cursor.execute(f"UPDATE iFood.usuario SET id_pedido = {ultimo_pedido} WHERE user_id = {usuario}")
	mydb.commit()
	
	# print(ultimo_pedido)

def carregar_pedido():
	global id_do_pedido
	usuario = session.get("user")
	my_cursor.execute(f"SELECT id_pedido FROM ifood.usuario WHERE user_id = {usuario} ")
	id_do_pedido = my_cursor.fetchall()[0][0]
		
def pegar_pedido_do_id():
	global sucesso
	usuario = session.get("user")
	my_cursor.execute(f"SELECT pedido_id from ifood.pedido WHERE user_id = {usuario}")
	sucesso = my_cursor.fetchall()
	
# def sucesso():
# 	global teste_sucesso
# 	teste_sucesso = 1
# 	time.sleep(3)
# 	return redirect("/inicio")

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
	pegar_pedido_do_id()
	usuario  = session.get("user")
	my_cursor.execute(f"SELECT nome FROM iFood.usuario WHERE user_id = {usuario}")
	nome = my_cursor.fetchall()[0][0]
	carregar_cesta()
	carregar_restaurantes()

	return render_template("home.html", nome=nome, restaurantes=restaurantes, vcesta=vcesta_formatado, sucesso=sucesso)

@app.route("/cesta")
def exibir_cesta():
	if not session.get("user"):
		return redirect("/entrar")
	pegarnome()
	carregar_cesta()
	return render_template('cesta.html', vcesta=vcesta_formatado, nome=nome, cesta_completa = cesta_completa)


@app.route("/registrando/cesta")
def gerar_pedido():
	pegar_pedido_do_id()
	if sucesso == []:
		gerar_pedido_banco()
		return redirect("/finalizar")
	
	return redirect("/inicio")

@app.route("/finalizar")
def finalizar_cesta():
	pegarnome()
	carregar_pedido()
	carregar_cesta()
	# print(f"O pedido carregado foi esse aqui {salvar_pedido}")
	usuario  = session.get("user")
	my_cursor.execute(f"SELECT * FROM ifood.endereco WHERE id_cliente = {usuario}")
	end_cadastrado= my_cursor.fetchall()
	return render_template("Finalizar.html",vcesta=vcesta_formatado, nome=nome, end_cadastrado=end_cadastrado, id_do_pedido=id_do_pedido)

@app.route("/atualizar/pedido/<id>")
def atualizar_pedido(id):
	usuario  = session.get("user")
	# my_cursor.execute(f"DELETE FROM ifood.endereco WHERE id_endereco = {id}")
	my_cursor.execute(f"UPDATE ifood.pedido set status = 'Aberto', endereco = {id}")
	mydb.commit()

	my_cursor.execute(f"delete from iFood.cesta where id_cliente = {usuario};")
	mydb.commit()

	
	return redirect("/inicio")

@app.route("/restaurante/<id>")
def entrar_restaurante(id):
	carregar_cesta()
	carregar_restaurantes()
	my_cursor.execute(f"SELECT * FROM iFood.restaurante WHERE id = {id}")
	salvando = my_cursor.fetchall()
	my_cursor.execute(f"SELECT * FROM ifood.itens WHERE id_restaurante = {id}")
	produtos = my_cursor.fetchall()
	return render_template("restaurante.html", salvando=salvando, produtos=produtos, vcesta=vcesta_formatado)
	

@app.route("/item/cesta/<id>/<res>")
def inserir_cesta(id, res):
	usuario = session.get("user")
	my_cursor.execute(f"SELECT * FROM ifood.itens WHERE id = {id}")
	ler = my_cursor.fetchall()
	img= ler[0][3]
	valor = ler[0][4]
	my_cursor.execute(f"INSERT INTO ifood.cesta (id_cliente, valor_cesta, id_item, id_restaurante, img_produto) VALUES ({usuario}, {valor}, {id}, {res}, '{img}')")
	mydb.commit()
	print(ler)
	print(valor)
	return redirect(f"/restaurante/{res}") 

@app.route("/remover/cesta/<id>")
def remover_cesta(id):
	my_cursor.execute(f"DELETE FROM ifood.cesta WHERE id_cesta = {id}")
	mydb.commit()
	return redirect("/cesta")

@app.route("/remover/endereco/<id>")
def remover_endereco(id):
	my_cursor.execute(f"DELETE FROM ifood.endereco WHERE id_endereco = {id}")
	mydb.commit()
	return redirect("/meus_dados")

@app.route("/buscando", methods=["POST"])
def buscar_res():
	buscar_restaurante()
	return redirect("/busca")

@app.route("/busca")
def busca_fin():
	pegarnome()
	carregar_cesta()
	return render_template("busca.html", valorbus=valorbus, nome=nome, vcesta=vcesta_formatado)


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
		carregar_cesta()
		carregar_meus_restaurantes()
		usuario  = session.get("user")
		# my_cursor.execute(f"SELECT endereco FROM iFood.usuario WHERE user_id = {usuario}")
		my_cursor.execute(f"SELECT * FROM ifood.endereco WHERE id_cliente = {usuario}")
		end_cadastrado= my_cursor.fetchall()
		print("-------------------LOG ENDEREÇO CAD-------------------------")
		print(f"Endereço: {end_cadastrado}")
		print("------------------------------------------------------------")
		return render_template("mdados.html", nome=nome, end_cadastrado=end_cadastrado, meus_restaurantes=meus_restaurantes, vcesta=vcesta_formatado)


	else:
		global retornar_endereco
		global numerocep
		coletarcep = request.form.get("cep")
		numerocep = request.form.get("numero")
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
	
