# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 13:24:37 2020

@author: Prakash.Gore
"""


import mysql.connector


db_connection = mysql.connector.connect(
  host="172.30.93.225",
  user="sepsis",
  passwd="Success_2020",
  database="sepsis"
)


# creating database_cursor to perform SQL operation
db_cursor = db_connection.cursor()
# executing cursor with execute method and pass SQL query
student_sql_query = "select * from student"
db_cursor.execute(student_sql_query)

myresult = db_cursor.fetchall()

for x in myresult:
  print(x)
#Get database table'
#db_cursor.execute(student_sql_query)
#db_connection.commit()
#print(db_cursor.rowcount, "Record Inserted")
print(db_connection)
