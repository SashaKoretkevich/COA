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
    created_at timestamp default current_timestamp,
    updated_at timestamp default null,
    deleted_at timestamp default null,
    isPrivate boolean default false,
    tags text[]
);

create table likes
(
    likeId SERIAL PRIMARY KEY,
    userId int not null,
    postId int not null,
    added_at timestamp default current_timestamp,
    deleted_at timestamp default null,
    foreign key (postId) references posts(postId),
    UNIQUE (userId, postId)
);

create table comments
(
    commentId SERIAL PRIMARY KEY,
    postId int not null,
    userId int not null,
    text varchar(255) not null,
    created_at timestamp default current_timestamp,
    deleted_at timestamp default null,
    foreign key (postId) references posts(postId)
);
''';
cursor.execute(sql)
conn.commit()
# cursor.execute("drop table likes")
# conn.commit()
# cursor.execute("drop table comments")
# conn.commit()
# cursor.execute("drop table posts")
# conn.commit()

cursor.close()
conn.close()