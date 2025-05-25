import pytest
import time
from fastapi.testclient import TestClient
from APIGateway.main import api
from APIGateway.models import userCreate, userLogin, userUpdate, postCreate
import os
from dotenv import load_dotenv
import psycopg2
import json
import clickhouse_connect


load_dotenv()

conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))

conn1 = psycopg2.connect(dbname=os.getenv("DBNAME1"), user=os.getenv("USER1"), 
                        password=os.getenv("PASSWORD1"), port=os.getenv("PORT1"), host=os.getenv("HOST1"))

conn2 = clickhouse_connect.get_client(
    host=os.getenv("DBNAME2"),
    port=os.getenv("PORT2"),
    username=os.getenv("USER2"),
    password=os.getenv("PASSWORD2")
)

client = TestClient(api)


user_data = userCreate(
    firstName="John",
    secondName="Doe",
    userName="user1",
    mail="user3@example.com",
    password="password123",
    age=30,
    gender="Male",
    status="Active",
    phoneNumber="+78004003377"
)

login_data = userLogin(mail="user3@example.com", password="password123")


post_data = postCreate(
    title="pupupu", 
    description="stringaaaaaa",
    isPrivate=True,
    tags=["Male", "Female"]
)

@pytest.fixture
def userRegister():
    response = client.post("/register", json=user_data.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    assert json_response is not None
    return json_response

@pytest.fixture
def userRegister1():
    response = client.post("/register", json=user_data1.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    assert json_response is not None
    return json_response

@pytest.fixture
def userLogin():
    response = client.post("/login", json=login_data.model_dump())
    assert response.status_code == 200
    token = response.cookies.get("access_token")
    assert token is not None
    return token

@pytest.fixture
def userLogin1():
    response = client.post("/login", json=login_data1.model_dump())
    assert response.status_code == 200
    token = response.cookies.get("access_token")
    assert token is not None
    return token

def testUnauthorizedAccess():
    response1 = client.post("/logout")
    assert response1.status_code == 200
    with pytest.raises(Exception) as excinfo:
        response = client.get("/stats/1")
    assert "401" in str(excinfo.value)

def test_get_post_stats(userRegister,userLogin):
    global post_id
    response = client.post("/posts", json=post_data.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    post_id = int(json_response["postId"])

    response = client.get(f"/posts/{post_id}/view")
    assert response.status_code == 200
    time.sleep(5)
    response = client.post(f"/posts/{post_id}/like")
    assert response.status_code == 200
    time.sleep(5)
    response = client.post(f"/posts/{post_id}/comment", params={'text': 'Test'})
    assert response.status_code == 200
    time.sleep(5)
    response4 = client.get(f"/stats/{post_id}")
    assert response4.status_code == 200
    json_data4 = response4.json()
    assert json_data4["views"] == 1
    assert json_data4["likes"] == 1
    assert json_data4["comments"] == 1


def test_get_post_views_by_day():
    response = client.get(f"/stats/{post_id}/views")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["stats"][0]["count"] == 1


def test_get_post_likes_by_day():
    response = client.get(f"/stats/{post_id}/views")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["stats"][0]["count"] == 1


def test_get_post_comments_by_day():
    response = client.get(f"/stats/{post_id}/views")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["stats"][0]["count"] == 1


def test_get_top_posts_likes():
    response = client.get("/stats/likes/top-posts")
    assert response.status_code == 200
    assert "posts" in response.json()

def test_get_top_posts_views():
    response = client.get("/stats/views/top-posts")
    assert response.status_code == 200
    assert "posts" in response.json()

def test_get_top_posts_comments():
    response = client.get("/stats/comments/top-posts")
    assert response.status_code == 200
    assert "posts" in response.json()

def test_get_top_users_comments():
    response = client.get("/stats/comments/top-users")
    assert response.status_code == 200
    assert "users" in response.json()

def test_get_top_users_likes():
    response = client.get("/stats/likes/top-users")
    assert response.status_code == 200
    assert "users" in response.json()

def test_get_top_users_views():
    response = client.get("/stats/views/top-users")
    assert response.status_code == 200
    assert "users" in response.json()
    cur = conn.cursor()
    cur.execute("select userId from auth where mail = 'user3@example.com'")
    userId = cur.fetchone()
    cur = conn.cursor()
    cur.execute("select userId from auth where mail = 'user3@example.com'")
    userId = cur.fetchone()
    cur.execute('delete from auth where userId = %s',(userId) )
    conn.commit()
    conn.close()
    cur1 = conn1.cursor()
    cur1.execute('delete from comments where userId = %s',(userId) )
    conn1.commit()
    cur1.execute('delete from likes where userId = %s',(userId) )
    conn1.commit()
    cur1.execute('delete from posts where userId = %s',(userId) )
    conn1.commit()
    conn1.close()
    conn2.command(f"ALTER TABLE views DELETE WHERE postId = {post_id}")
    conn2.command(f"ALTER TABLE likes DELETE WHERE postId = {post_id}")
    conn2.command(f"ALTER TABLE comments DELETE WHERE postId = {post_id}")


