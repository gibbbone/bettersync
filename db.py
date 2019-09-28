import os
import sqlite3
from datetime import datetime

# create a default path to connect to and create (if necessary) a database
# called 'database.sqlite3' in the same directory as this script

#DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')
DEFAULT_PATH = os.path.join(os.getcwd(), 'data', 'history.db') 
DEFAULT_START_FILE = os.path.join(os.getcwd(), 'data', 'path_list.csv') 

def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con

def reset_dataset(con):
    """WARNING: this will delete both tables in the dataset"""
    # instantiate a cursor obj
    cur = con.cursor() 
    cur.execute("DROP TABLE paths")
    cur.execute("DROP TABLE commands")

def create_tables(con):    
    try:
        # instantiate a cursor obj
        cur = con.cursor() 
        paths = """
        CREATE TABLE paths (
            id integer PRIMARY KEY,
            path text NOT NULL)"""
        cur.execute(paths)
        commands = """
        CREATE TABLE commands (
            id integer PRIMARY KEY,
            date text NOT NULL,
            source_path_id integer NOT NULL,
            target_path_id integer NOT NULL,
            FOREIGN KEY (source_path_id) REFERENCES paths (id), 
            FOREIGN KEY (target_path_id) REFERENCES paths (id))"""
        cur.execute(commands)
        con.commit()
        return
    except:
        # rollback all database actions since last commit
        con.rollback()
        raise RuntimeError("An error occurred. Rolled back.")      

def create_path(con, path):
    cur = con.cursor()
    path_sql = "INSERT INTO paths (path) VALUES (?)"
    cur.execute(path_sql, (path,))
    return cur.lastrowid

def create_command(con, date, source_id, target_id):
    cur = con.cursor()
    command_sql = """
        INSERT INTO commands (date, source_path_id, target_path_id) 
        VALUES (?,?,?)"""
    cur.execute(command_sql, (date, source_id, target_id))
    return cur.lastrowid

def get_path_id(con, path):
    cur = con.cursor()
    cur.execute("SELECT id FROM paths WHERE path = '{}'".format(path))
    result = cur.fetchone()
    return result

def create_rsync_record(con, p1, p2):
    try:
        if get_path_id(con,p1) is None:
            p1_id = create_path(con, p1)
            con.commit()   

        if get_path_id(con,p2) is None:
            p2_id = create_path(con, p2)
            con.commit()    
        time = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        c1_id = create_command(con, time, get_path_id(con,p1)[0], get_path_id(con,p2)[0])
        con.commit()
        return
    except:
        # rollback all database actions since last commit
        con.rollback()
        raise RuntimeError("An error occurred. Rolled back.")        

def get_source_paths(con):
    cur = con.cursor()
    sql_command = """
        SELECT DISTINCT path FROM paths 
        INNER JOIN commands on commands.source_path_id=paths.id"""
    cur.execute(sql_command)
    results = cur.fetchall()
    return [r[0] for r in results]

def get_target_paths(con):
    cur = con.cursor()
    sql_command = """
        SELECT DISTINCT path FROM paths 
        INNER JOIN commands on commands.target_path_id=paths.id"""
    cur.execute(sql_command)
    results = cur.fetchall()
    return [r[0] for r in results]