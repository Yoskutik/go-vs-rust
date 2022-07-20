import mysql.connector
import subprocess
import sqlite3
import shutil
import random
import time
import sys
import csv
import os

from pathlib import Path


def prepare_text_data():
    print('Preparing text files...', end='')
    shutil.rmtree('init-text-data', ignore_errors=True)
    os.mkdir('init-text-data')
    for x in range(20):
        with open(f'init-text-data/{x}.txt', 'w') as file:
            file.writelines(['0' * 63 + '\n'] * (x + 1) * 3)
    print('\b\b\b: Done')


def prepare_databases():
    print('Preparing databases...', end='')

    mysql_db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="database"
    )

    mysql_cursor = mysql_db.cursor()

    create_sql = 'CREATE TABLE users (id INT PRIMARY KEY NOT NULL, salary INT NOT NULL, age INT NOT NULL, address CHAR(50))'
    insert_sql = "INSERT INTO users (id, salary, age, address) VALUES (%s, %s, %s, 'Somewhere')"
    Path('init-database.db').unlink(missing_ok=True)
    sqlite_db = sqlite3.connect('init-database.db')
    sqlite_db.execute(create_sql)
    mysql_cursor.execute('DROP TABLE IF EXISTS users')
    mysql_cursor.execute(create_sql)
    random.seed(0)
    for x in range(10000):
        salary = random.randint(0, 200)
        age = random.randint(0, 99)
        sqlite_db.execute(f"INSERT INTO users (id, salary, age, address) VALUES ({x}, {salary}, {age}, 'Somewhere')")
        mysql_cursor.execute(insert_sql, (x, salary, age))
    sqlite_db.commit()
    mysql_db.commit()
    sqlite_db.close()
    os.environ['MYSQL_PWD'] = 'root'
    subprocess.run('mysqldump -u root database > migrate.sql', shell=True)
    print('\b\b\b: Done')


def update_text_data():
    shutil.rmtree('data', ignore_errors=True)
    shutil.copytree('init-text-data', 'data')


def update_sqlite():
    for x in ['database.db', 'database.db-shm', 'database.db-wal']:
        Path(x).unlink(missing_ok=True)
    shutil.copy('init-database.db', 'database.db')


def update_mysql():
    subprocess.run('mysql -u root database < migrate.sql', shell=True)
    

def delete_last_line():
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')


def save_data(data, name: str):
    with open(f'results/{name}.csv', 'w') as file:
        writer = csv.writer(file, delimiter=';', lineterminator='\n')
        writer.writerow(['n_routines'] + data['labels'])
        for power in range(6):
            n_routines = 10 ** (power + 1)
            writer.writerow([n_routines] + data[n_routines])


def cleanup():
    shutil.rmtree('data', ignore_errors=True)
    shutil.rmtree('init-text-data', ignore_errors=True)
    for x in ['database.db', 'database.db-shm', 'database.db-wal', 'init-database.db', 'migrate.sql']:
        Path(x).unlink(missing_ok=True)


def print_result(timers, memory, test_name):
    try:
        rust_index = timers["labels"].index(f'Rust: {test_name}')
        go_index = timers["labels"].index(f'Go: {test_name}')
    except ValueError:
        return
    
    def get_item(index, n_routines):
        secs = timers[n_routines][index]
        secs_text = f'{(secs / 1_000_000):,.3f}s'
        mem = memory[n_routines][index]
        mem_text = f'{(mem / 1024):.2f}Gb' if mem > 1000 else f'{mem:.2f}Mb'
        return f'| {secs_text:<7} | {mem_text:<8} '

    def get_diff(n_routines):
        time_diff = timers[n_routines][rust_index] / timers[n_routines][go_index] * 100 - 100
        time_diff = f'{"+" if time_diff > 0 else ""}{time_diff:.1f}%'
        mem_diff = memory[n_routines][rust_index] / memory[n_routines][go_index] * 100 - 100
        mem_diff = f'{"+" if mem_diff > 0 else ""}{mem_diff:.1f}%'
        return f'| {time_diff:<7} | {mem_diff:<7} |'

    print(f'{test_name} results:')
    print('+' + '-' * 11 + '+' + '-' * 20 + '+' + '-' * 20 + '+' + '-' * 19 + '+')
    print('| amount    ' + '|' + ' Rust' + ' ' * 15 + '|' + ' Go' + ' ' * 17 + '| Diff' + ' ' * 14 + '|')
    print('+' + '-' * 11 + '+' + '-' * 9 + '+' + '-' * 10 + '+' + '-' * 9 + '+' + '-' * 10 + '+' + '-' * 9 + '+' + '-' * 9 + '+')
        
    for x in range(6):
        n_routines = 10 ** (x + 1)
        if times[n_routines][go_index] == -1:
            break
        print(f'| {n_routines:<9,} {get_item(rust_index, n_routines)}{get_item(go_index, n_routines)}{get_diff(n_routines)}')
    print('+' + '-' * 11 + '+' + '-' * 9 + '+' + '-' * 10 + '+' + '-' * 9 + '+' + '-' * 10 + '+' + '-' * 9 + '+' + '-' * 9 + '+')
    print()


def print_results(timers, memory):
    for x in ['1. Sleep', '2. Files R', '3. Files RW', '4. SQLite', '5. MySQL']:
        print_result(timers, memory, x)
