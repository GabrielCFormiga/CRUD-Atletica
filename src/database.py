import psycopg2
import os
from dotenv import load_dotenv
from psycopg2 import Error

load_dotenv()

password = os.getenv('password')

def conecta():
    try:
        conn = psycopg2.connect(
            dbname="crud_compilada",
            user="campfor",
            password=password,
            host="localhost")

        # print("Conexão com o banco de dados realizada com sucesso")

        return conn

    except Error as e:
        print(f"Erro ao conectar com o banco de dados {e}")

def desconecta(conn):
    if conn:
        conn.close()
    # print("Conexão com o banco de dados fechada com sucesso")