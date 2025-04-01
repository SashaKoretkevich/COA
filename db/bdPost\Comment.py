import psycopg2
import os
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 
 
conn = psycopg2.connect(dbname=os.getenv("DBNAME1"), user=os.getenv("USER1"), 
                        password=os.getenv("PASSWORD1"), port=os.getenv("PORT1"), host=os.getenv("HOST1"))
 
conn.autocommit = True
 
cursor = conn.cursor()
 
sql = '''
create table posts
(
    postId SERIAL PRIMARY KEY,
    title varchar(255) not null,
    description varchar(255) not null,
    userId int not null,
    creationTime timestamp default current_timestamp,
    lastUpdate timestamp default current_timestamp,
    isPrivate boolean default false,
    tags text[]
);
''';
cursor.execute(sql)
# cursor.execute("drop table posts")
conn.commit()
print("Tables are created")

cursor.close()
conn.close()