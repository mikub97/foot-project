import sqlite3
import time
import traceback

import requests

sql_insert_traces = """Insert into traces (USERID,BIRTHDATE,DISABLED,FIRSTNAME,SECONDNAME,TRACENAME,TRACEID ,TRACETIME ,L0, L1, L2, R0, R1, R2) values (?,?,?,?,?,?,?,?,?, ?, ?, ?, ?,?);"""

sql_create_traces_table = """CREATE TABLE IF NOT EXISTS traces (
                                      userid integer NOT NULL,
                                      birthdate TEXT(10)  NULL,
                                      disabled INTEGER  NULL,
                                      firstname TEXT  NULL,
                                      secondname TEXT NULL,
                                      TRACEID TEXT NULL,
                                      TRACENAME TEXT NULL,
                                      TRACETIME REAL,
                                      L0 REAL, L1 REAL, L2 REAL, R0 REAL, R1 REAL, R2 REAL); """

sql_create_users_table = """CREATE TABLE IF NOT EXISTS users (
                                          userid integer NOT NULL,
                                          birthdate TEXT(10)  NULL,
                                          disabled INTEGER  NULL,
                                          firstname TEXT  NULL,
                                          secondname TEXT NULL); """
sql_insert_users = """Insert into users (USERID,BIRTHDATE,DISABLED,FIRSTNAME,SECONDNAME)
                          values (?,?,?,?,?);"""

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def static_user_info(conn):
    cur = conn.cursor();
    cur.execute("DROP TABLE IF EXISTS USERS")
    create_table(conn,sql_create_users_table);
    for user_id in range(1, 7):
        try:
            response = requests.get(f'http://tesla.iem.pw.edu.pl:9080/v2/monitor/{user_id}')
            data = response.json()
        except Exception:
            traceback.print_exc();
            print("Check the VPN connection")
            exit()
        birthdate = data["birthdate"]
        disabled = data["disabled"]
        firstname = data["firstname"]
        secondname = data["lastname"]
        uId = data["id"]
        cur.execute(sql_insert_users, (uId,birthdate,disabled,firstname,secondname));
    conn.commit();

def get_users(c) :
    c.execute("SELECT * FROM USERS")
    rows = c.fetchall()
    users=[]
    for row in rows:
        l = list(row);
        u={
            "id": l[0],
            "bithdate": l[1],
            "disabled": l[2],
            "firstname":l[3],
            "secondname": l[4]
        }
        users.append(u)

    return users;

def main():
    database = "realtime.db"
    conn = create_connection(database)
    static_user_info(conn)
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_traces_table)
    cur = conn.cursor()

    ID = 0
    while(True):
        for user_id in range(1,7):
            try:
                response = requests.get(f'http://tesla.iem.pw.edu.pl:9080/v2/monitor/{user_id}')
                data = response.json()
            except Exception :
                traceback.print_exc();
                print("Check the VPN connection")
                exit()
            birthdate = data["birthdate"]
            disabled = data["disabled"]
            firstname = data["firstname"]
            secondname = data["lastname"]
            uId = data["id"]
            traceId =  data["trace"]["id"]
            traceName= data["trace"]["name"]
            traceTime = time.time()
            L0 = data["trace"]["sensors"][0]["value"]
            L1 = data["trace"]["sensors"][1]["value"]
            L2 = data["trace"]["sensors"][2]["value"]
            R0 = data["trace"]["sensors"][3]["value"]
            R1 = data["trace"]["sensors"][4]["value"]
            R2 = data["trace"]["sensors"][5]["value"]
            ID = ID+1
            print(ID,traceTime, L0, L1, L2, R0, R1, R2)

            # """Insert into traces
            # (USERID,BIRTHDATE,DISABLED,FIRSTNAME,SECONDNAME,TRACENAME,TRACEID TRACETIME ,L0, L1, L2, R0, R1, R2) values (?,?,?,?,?,?,?,?,?, ?, ?, ?, ?,?);"""
            try:
                cur.execute(sql_insert_traces,(uId,birthdate,disabled,firstname,secondname,traceName,traceId,traceTime, L0, L1, L2, R0, R1, R2))

            except:
                traceback.print_exc();
                print("Unexpected Error")
                exit()
        conn.commit()
        time.sleep(1)
if __name__ == '__main__':
    main()