import pytest
from fastapi.testclient import TestClient
from APIGateway.main import api
from APIGateway.models import userCreate, userLogin, userUpdate, postCreate
import os
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv() 
 
conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), 
                        password=os.getenv("PASSWORD"), host=os.getenv("HOST"))

client = TestClient(api)

user_data_1 = userCreate(
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

login_data_1 = userLogin(mail="user3@example.com", password="password123")

update_data_1 = userUpdate(
    firstName="tyyttyyt", 
    secondName="string",
    age=30,
    gender="Male",
    status="string",
    phoneNumber="+78004003377"
)

post_data_1 = postCreate(
    title="pupupu", 
    description="stringaaaaaa",
    isPrivate=True,
    tags=["Male", "Female"]
)

post_update_1 = postCreate(
    title="hahaha", 
    description="stringaaaaaa",
    isPrivate=True,
    tags=["Male", "Female"]
)

@pytest.fixture
def userRegister():
    response = client.post("/register", json=user_data_1.model_dump())
    assert response.status_code == 200

@pytest.fixture
def userLogin():
    response = client.post("/login", json=login_data_1.model_dump())
    assert response.status_code == 200
    token = response.cookies.get("access_token")
    assert token is not None
    return token

#Проверка валедаторов

def testWrongAge():
    with pytest.raises(ValueError) as info:
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=5,
            gender="Male",
            status="Active",
            phoneNumber="+78004003377") 
    assert info.value.errors()[0]['msg'] == "Value error, Возраст должен быть больше 14 лет" 

def testWrongGender():
    with pytest.raises(ValueError) as info:  
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=30,
            gender="Cat",
            status="Active",
            phoneNumber="+78004003377") 
    assert info.value.errors()[0]['msg'] == "Value error, Неправильно указан пол"

def testWrongPhone():
    with pytest.raises(ValueError) as info:  
        userCreate(
            firstName="John",
            secondName="Doe",
            userName="user1",
            mail="user3@example.com",
            password="password123",
            age=30,
            gender="Male",
            status="Active",
            phoneNumber="+78004003") 
    assert info.value.errors()[0]['msg'] == 'Value error, Номер телефона должен начинаться с "+" и содержать 11 цифр' 

#Проверка workflow

def testRegLog(userRegister, userLogin):
    assert userLogin is not None

def testGetProfile():
    response = client.get("/profile")
    assert response.status_code == 200
    user = response.json()
    assert user["firstName"] == "John"

def testUpdateProfile():
    response = client.put("/profile", json=update_data_1.model_dump())
    assert response.status_code == 200
    response1 = client.get("/profile")
    user = response1.json()
    assert user["firstName"] == "tyyttyyt"

def testCreatePost():
    global post_id 
    response = client.post("/posts", json=post_data_1.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    post_id = int(json_response["postId"])
    assert "postId" in json_response
    assert json_response["postId"] > 0

def testGetPost():
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["title"] == "pupupu"
    assert json_response["description"] == "stringaaaaaa"

def testListPosts():
    response = client.post("/posts", json=post_data_1.model_dump())
    response = client.post("/posts", json=post_data_1.model_dump())

    response = client.get("/posts?limit=3&offset=0")

    assert response.status_code == 200
    json_response = response.json()
    assert "posts" in json_response
    assert len(json_response["posts"]) == 3

def testUnauthorized():
    client.post("/logout")
    with pytest.raises(Exception) as excinfo:
        client.post("/posts", json=post_data_1.model_dump())
    assert "401" in str(excinfo.value)

def testUpdatePost(userLogin):
    response = client.put(f"/posts/{post_id}", json=post_update_1.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    assert "postId" in json_response
    assert json_response["title"] == "hahaha"

def testDeletePost():
    response1 = client.delete(f"/posts/{post_id}")
    response2 = client.delete(f"/posts/{post_id + 1}")
    response3 = client.delete(f"/posts/{post_id + 2}")
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    json_response1 = response1.json()
    json_response2 = response2.json()
    json_response3 = response3.json()
    assert "postId" in json_response1
    assert "postId" in json_response2
    assert "postId" in json_response3
    assert json_response1["postId"] == post_id
    assert json_response2["postId"] == post_id + 1
    assert json_response3["postId"] == post_id + 2


def testLogout(userLogin):
    response = client.post("/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    cur = conn.cursor()
    cur.execute("select userId from auth where mail = 'user3@example.com'")
    userId1 = cur.fetchone()
    cur.execute('delete from auth where userId = %s',(userId1, ) )
    conn.commit()
    cur.close()
    conn.close()

