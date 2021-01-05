import math
import sqlite3
import json
import time

import requests

import data_importing as di

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
    except sqlite3.Error as e:
        print(e)


def get_measure_tuple(id):
     t = time.time()
     response = requests.get(f'http://tesla.iem.pw.edu.pl:9080/v2/monitor/{id}')
     measure = response.json()
     return {
         'measure' : (measure['birthdate'],measure['disabled'],measure['firstname']
                      ,measure['lastname'],measure['id'],measure['trace']['id'],
                      t),
         'trace' : (measure['trace']['id'],measure['trace']['name'],json.dumps(measure['trace']['sensors']))
     }


def main():

    database = "test.db"
    sql_create_traces_table =""" CREATE TABLE IF NOT EXISTS traces (
                                        id integer PRIMARY KEY,  
                                        name text Null,
                                        sensors json
                                    ); """

    sql_create_measurements_table = """ CREATE TABLE IF NOT EXISTS measurements (
                                        birthdate TEXT(10) NOT NULL,
                                        disabled INTEGER NOT NULL,
                                        firstname TEXT NOT NULL,
                                        secondname TEXT NOT NULL,
                                        id INTEGER NOT NULL,
                                        trace_id integer NOT NULL,
                                        measure_time TIMESTAMP NOT NULL, 
                                        FOREIGN KEY (trace_id) REFERENCES traces (id)
                                    ); """
    sql_insert_traces= """INSERT INTO traces('id','name','sensors')
                              VALUES (?, ?,?);"""
    sql_insert_measurements= """INSERT INTO 'measurements'('birthdate','disabled','firstname','secondname','id',
                              'trace_id','measure_time') 
                              VALUES (?, ?,?,?,?,?,?);"""

    conn = create_connection(database)
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_traces_table)

        # create tasks table
        create_table(conn, sql_create_measurements_table)
    else:
        print("Error! cannot create the database connection.")

    cursor = conn.cursor()

    for i in range(1,5):
        m=get_measure_tuple(i)
        cursor.execute(sql_insert_traces,m['trace'])
        cursor.execute(sql_insert_measurements,m['measure'])

    conn.commit()
if __name__ == '__main__':
    main()

