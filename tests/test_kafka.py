import pytest
from fastapi.testclient import TestClient
from APIGateway.main import api
from APIGateway.models import userCreate, userLogin, userUpdate, postCreate
import os
from dotenv import load_dotenv
import psycopg2
import json

conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))

conn1 = psycopg2.connect(dbname=os.getenv("DBNAME1"), user=os.getenv("USER1"), 
                        password=os.getenv("PASSWORD1"), port=os.getenv("PORT1"), host=os.getenv("HOST1"))

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

user_data1 = userCreate(
    firstName="John1",
    secondName="Doe1",
    userName="user11",
    mail="user31@example.com",
    password="password1231",
    age=30,
    gender="Male",
    status="Active",
    phoneNumber="+78004003377"
)

login_data1 = userLogin(mail="user31@example.com", password="password1231")

login_data = userLogin(mail="user3@example.com", password="password123")

update_data = userUpdate(
    firstName="tyyttyyt", 
    secondName="string",
    age=30,
    gender="Male",
    status="string",
    phoneNumber="+78004003377"
)

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

def testUserRegister(userRegister):
    assert userRegister is not None

def testUnauthorizedView():
    response1 = client.post("/logout")
    assert response1.status_code == 200
    with pytest.raises(Exception) as excinfo:
        response = client.get(f"/posts/0/view")
    assert "401" in str(excinfo.value)

def testNotFindView(userLogin):
    assert userLogin is not None
    with pytest.raises(Exception) as excinfo:
        response = client.get(f"/posts/0/view")
    assert "404" in str(excinfo.value)

def testDeniedAccessView(userRegister1, userLogin1):
    assert userLogin1 is not None
    global post_id1 

    response = client.post("/posts", json=post_data.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    post_id1 = int(json_response["postId"])

    response = client.post("/login", json=login_data.model_dump())
    assert response.status_code == 200

    with pytest.raises(Exception) as excinfo:
        response = client.get(f"/posts/{post_id1}/view")
    assert "403" in str(excinfo.value)

def testViewPost(userLogin):
    global post_id
    assert userLogin is not None
    response = client.post("/posts", json=post_data.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    post_id = int(json_response["postId"])

    response = client.get(f"/posts/{post_id}/view")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["title"] == "pupupu"
    assert json_response["description"] == "stringaaaaaa"

def testLikePost():
    response = client.post(f"/posts/{post_id}/like")
    assert response.status_code == 200

def testDoubleLikePost():
    with pytest.raises(Exception) as excinfo:
        client.post(f"/posts/{post_id}/like")
    assert "409" in str(excinfo.value)

def testCommentPost():
    response = client.post(f"/posts/{post_id}/comment", params={'text': 'Test'})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["text"] == "Test"


def testListComments():
    response = client.get(f"/posts/{post_id}/comment", params={'limit': 1, 'offset': 0})
    assert response.status_code == 200
    json_response = response.json()
    assert "comments" in json_response
    assert len(json_response["comments"]) == 1
    cur = conn.cursor()
    cur.execute("select userId from auth where mail = 'user3@example.com'")
    userId = cur.fetchone()
    cur.execute("select userId from auth where mail = 'user31@example.com'")
    userId1 = cur.fetchone()
    cur.execute('delete from auth where userId = %s or userId = %s',(userId1, userId) )
    conn.commit()
    conn.close()
    cur1 = conn1.cursor()
    cur1.execute('delete from comments where userId = %s or userId = %s',(userId1, userId) )
    conn1.commit()
    cur1.execute('delete from likes where userId = %s or userId = %s',(userId1, userId) )
    conn1.commit()
    cur1.execute('delete from posts where userId = %s or userId = %s',(userId1, userId) )
    conn1.commit()
    conn1.close()
    

