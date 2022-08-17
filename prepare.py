import mysql.connector
import subprocess
import psycopg2
import logging
import sqlite3
import shutil
import random
import os
from pathlib import Path


log_level = 0


def log_wrap(name: str, deep=False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal name
            global log_level
            title = f'Preparing {name}...' if not deep else f'Starting prepare {name}:'
            if log_level > 0:
                title = f'{"|  " * (log_level - 1)}+ {title}'
            print(title, end='' if not deep else '\n')
            log_level += 1
            func(*args, **kwargs)
            log_level -= 1
            if not deep:
                print('\b\b\b: Done.')
            else:
                print(f'{"|  " * log_level}Preparing {name} is done.')
        return wrapper
    return decorator


def _prepare_any_db(db, create_query: str, insert_query: str, data) -> None:
    cursor = db.cursor()
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute(create_query)
    for id, row in enumerate(data):
        cursor.execute(insert_query % (id, *row))
    db.commit()
    cursor.close()
    db.close()


@log_wrap('text files')
def _prepare_text_data() -> None:
    shutil.rmtree('init-text-data', ignore_errors=True)
    os.mkdir('init-text-data')
    for x in range(20):
        with open(f'init-text-data/{x}.txt', 'w') as file:
            file.writelines(['0' * 63 + '\n'] * (x + 1) * 3)


@log_wrap('SQLite')
def _prepare_sqlite(create_query: str, insert_query: str, data) -> None:
    Path('init-database.db').unlink(missing_ok=True)
    db = sqlite3.connect('init-database.db')
    _prepare_any_db(db, create_query, insert_query, data)
    

@log_wrap('MySQL')
def _prepare_mysql(create_query: str, insert_query: str, data) -> None:
    os.environ['MYSQL_PWD'] = 'root'
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="database"
    )
    _prepare_any_db(db, create_query, insert_query, data)
    subprocess.run('mysqldump -u root database > migrate_mysql.sql', shell=True)


@log_wrap('PostgreSQL')
def _prepare_postgresql(create_query: str, insert_query: str, data) -> None:
    os.environ['PGPASSWORD'] = 'root'
    db = psycopg2.connect(dbname='postgres', user='postgres', password='1', host='localhost')
    _prepare_any_db(db, create_query, insert_query, data)
    subprocess.run('pg_dump -U postgres --clean > migrate_postgresql.sql', shell=True)
    

@log_wrap('databases', True)
def _prepare_databases() -> None:
    create_query = '''
        CREATE TABLE users (
            id INT PRIMARY KEY NOT NULL,
            salary INT NOT NULL,
            age INT NOT NULL,
            address CHAR(50)
        )
    '''
    insert_query = '''
        INSERT INTO users (id, salary, age, address)
        VALUES (%s, %s, %s, 'Somewhere')
    '''
    random.seed(0)
    data = [(random.randint(0, 200), random.randint(0, 99)) for x in range(10_000)]
    _prepare_sqlite(create_query, insert_query, data)
    _prepare_mysql(create_query, insert_query, data)
    _prepare_postgresql(create_query, insert_query, data)


@log_wrap('data', True)
def prepare_data() -> None:
    _prepare_text_data()
    _prepare_databases()


def update_text_data() -> None:
    shutil.rmtree('data', ignore_errors=True)
    shutil.copytree('init-text-data', 'data')


def update_sqlite() -> None:
    for x in ['database.db', 'database.db-shm', 'database.db-wal']:
        Path(x).unlink(missing_ok=True)
    shutil.copy('init-database.db', 'database.db')
    os.environ['DATABASE_URL'] = f'sqlite:{os.getcwd()}/database.db'


def update_mysql() -> None:
    subprocess.run('mysql -u root database < migrate_mysql.sql', shell=True)
    os.environ['DATABASE_URL'] = 'mysql://root:root@localhost/db'


def update_postgresql() -> None:
    subprocess.run('psql -U postgres < migrate_postgresql.sql', shell=True, stdout=subprocess.DEVNULL)
    os.environ['DATABASE_URL'] = 'postgres://root:root@localhost/db'


def cleanup() -> None:
    shutil.rmtree('data', ignore_errors=True)
    shutil.rmtree('init-text-data', ignore_errors=True)
    for x in ['database.db', 'database.db-shm', 'database.db-wal', 'init-database.db', 'migrate_mysql.sql',
              'migrate_postgresql.sql']:
        Path(x).unlink(missing_ok=True)
