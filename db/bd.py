import psycopg2
import os
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 
 
conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))
 
conn.autocommit = True
 
cursor = conn.cursor()
 
sql = '''

create table auth
(
    userId SERIAL PRIMARY KEY,
    userName varchar(255) unique not null,
    mail varchar(255) unique not null,
    password varchar(255) not null
);

create table users
(
    userId int primary key,
    firstName varchar(255) not null,
    secondName varchar(255) not null,
    age int check (age >= 14),
    gender varchar(50) check (gender in ('Male', 'Female')),
    status varchar(255),
    phoneNumber varchar(20),
    creationTime timestamp default current_timestamp,
    lastUpdate timestamp default current_timestamp,
    foreign key (userId) references auth(userId) on delete cascade
);
''';
cursor.execute(sql)
conn.commit()
print("Tables are created")

cursor.close()
conn.close()