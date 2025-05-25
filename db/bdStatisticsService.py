import clickhouse_connect
import os
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 
 
client = clickhouse_connect.get_client(
    host=os.getenv("DBNAME2"),
    port=os.getenv("PORT2"),
    username=os.getenv("USER2"),
    password=os.getenv("PASSWORD2")
)

client.command('''
create table if not exists views (
    timestamp DateTime,
    postId Int64,
    userId Int64
) engine = MergeTree()
order by (postId, timestamp)
''')

client.command('''
create table if not exists likes (
    timestamp DateTime,
    postId Int64,
    userId Int64
) engine = MergeTree()
order by (postId, timestamp)
''')

client.command('''
create table if not exists comments (
    timestamp DateTime,
    postId Int64,
    userId Int64
) engine = MergeTree()
order by (postId, timestamp)
''')

# client.command("DROP TABLE views")
# client.command("DROP TABLE likes")
# client.command("DROP TABLE comments")
