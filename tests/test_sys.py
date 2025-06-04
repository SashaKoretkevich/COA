import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, Mock
from PostService.grpcSev import PostService
from protos import pcsev_pb2, pcsev_pb2_grpc, stat_pb2, stat_pb2_grpc
from StatisticService.grpcSev import StatisticsService
from fastapi import HTTPException
from UserService.app.users import users, register, login, updateProfile
from UserService.app.auth import createToken
from UserService.app.models import userCreate, userLogin, userUpdate, tokenSend
from datetime import datetime
from fastapi import FastAPI
from APIGateway.main import api
from google.protobuf.timestamp_pb2 import Timestamp
import StatisticService.kafkaConsumer as consumer
import json
from freezegun import freeze_time

app1 = FastAPI()
app1.include_router(api)
client1 = TestClient(app1)
client = TestClient(users)

class DummyMessage:
    def __init__(self, topic, value_bytes):
        self._topic = topic
        self._value = value_bytes
    def topic(self):
        return self._topic
    def value(self):
        return self._value

@pytest.fixture
def grpc_context():
    return MagicMock()

@patch("PostService.grpcSev.dbConn")
def test_create_post_saves_to_db(mock_db_conn, grpc_context):
    service = PostService()
    request = pcsev_pb2.CreatePostRequest(
        title="Test Title",
        description="Test Description",
        userId=1,
        isPrivate=False,
        tags=["tag1", "tag2"]
    )

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.side_effect = [
        (123,),
        (123, "Test Title", "Test Description", 1, "2024-01-01", "2024-01-02", None, False, ['tag1', 'tag2']) 
    ]

    response = service.CreatePost(request, grpc_context)

    mock_cursor.execute.assert_any_call(
        "insert into posts (title, description, userid, created_at, isPrivate, tags) values (%s, %s, %s, now(), %s, %s) returning postId;",
        ("Test Title", "Test Description", 1, False, '{"tag1","tag2"}')
    )
    mock_conn.commit.assert_called_once()
    assert response.postId == 123
    assert response.title == "Test Title"


@patch("PostService.grpcSev.dbConn")
def test_get_post_returns_correct_data(mock_db_conn, grpc_context):
    service = PostService()
    request = pcsev_pb2.GetPostRequest(postId=123, userId=1)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = (123, "Title", "Desc", 1, "2024-01-01", "2024-01-02", None, False, ["tag"])

    response = service.GetPost(request, grpc_context)

    mock_cursor.execute.assert_called_with(
        "select * from posts where postid = %s and deleted_at is null;", (123,)
    )
    assert response.postId == 123
    assert response.title == "Title"


@patch("PostService.grpcSev.dbConn")
def test_update_post_executes_update(mock_db_conn, grpc_context):
    service = PostService()
    request = pcsev_pb2.UpdatePostRequest(
        postId=123,
        title="New Title",
        description="Updated",
        userId=1,
        isPrivate=True,
        tags=["a", "b"]
    )

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.side_effect = [
        (123, "Old Title", "Old Desc", 1, "2024-01-01", "2024-01-01", None, False, ["old"]),
        (123, "New Title", "Updated", 1, "2024-01-01", "2024-01-02", None, True, ["a", "b"]),
    ]

    response = service.UpdatePost(request, grpc_context)

    mock_cursor.execute.assert_any_call(
        "update posts set title = %s, description = %s, updated_at = now(), isPrivate = %s, tags = %s where postid = %s and deleted_at is null;",
        ("New Title", "Updated", True, '{"a","b"}', 123)
    )
    mock_conn.commit.assert_called()
    assert response.title == "New Title"
    assert response.isPrivate is True

@patch("StatisticService.grpcSev.client")
def test_get_post_stats(mock_client, grpc_context):
    mock_client.query.side_effect = [
        MagicMock(result_rows=[(10,)]),
        MagicMock(result_rows=[(5,)]),
        MagicMock(result_rows=[(2,)])
    ]

    service = StatisticsService()
    request = stat_pb2.PostRequest(postId=1)

    response = service.GetPostStats(request, grpc_context)

    assert response.views == 10
    assert response.likes == 5
    assert response.comments == 2
    assert mock_client.query.call_count == 3
    mock_client.query.assert_any_call("select count() from views where postId = '1'")
    mock_client.query.assert_any_call("select count() from likes where postId = '1'")
    mock_client.query.assert_any_call("select count() from comments where postId = '1'")


@patch("StatisticService.grpcSev.client")
def test_get_post_views_by_day(mock_client, grpc_context):
    mock_client.query.return_value.named_results.return_value = [
        {'date': '2024-06-01', 'cnt': 3},
        {'date': '2024-06-02', 'cnt': 5},
    ]

    service = StatisticsService()
    request = stat_pb2.PostRequest(postId=1)

    response = service.GetPostViewsByDay(request, grpc_context)

    assert len(response.stats) == 2
    assert response.stats[0].date == '2024-06-01'
    assert response.stats[0].count == 3
    assert response.stats[1].count == 5
    mock_client.query.assert_called_once()
    assert "views" in mock_client.query.call_args[0][0]


@patch("StatisticService.grpcSev.client")
def test_get_top_posts_by_metric(mock_client, grpc_context):
    mock_client.query.return_value.named_results.return_value = [
        {'postId': 1, 'cnt': 10},
        {'postId': 2, 'cnt': 8},
    ]

    service = StatisticsService()
    request = stat_pb2.MetricRequest(metric="likes")

    response = service.GetTopPostsByMetric(request, grpc_context)

    assert len(response.posts) == 2
    assert response.posts[0].postId == 1
    assert response.posts[0].count == 10
    assert "likes" in mock_client.query.call_args[0][0]

def test_register_success(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.side_effect = [None, None, (42,)]
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
  
    monkeypatch.setattr('UserService.app.users.connection', fake_conn)
    
    monkeypatch.setattr('UserService.app.users.kafka_producer.send_user_registered_event', lambda user_id: None)

    monkeypatch.setattr("UserService.app.auth.pwToHash", lambda pw: 'hashed_pw')

    data = {
        "userName": "testuser",
        "mail": "test@example.com",
        "password": "pass123r4r34rrer",
        "firstName": "John",
        "secondName": "Doe",
        "age": 30,
        "gender": "Male",
        "status": "active",
        "phoneNumber": "+71234567890"
    }
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert response.json() == {
        "id": 42,
        "username": "testuser",
        "email": "test@example.com"
    }

    fake_cursor.execute.assert_any_call('select * from auth where mail= %s', ('test@example.com',))
    fake_cursor.execute.assert_any_call('select * from auth where userName= %s', ('testuser',))
    # fake_cursor.execute.assert_any_call("insert into auth (userName, mail, password) values (%s, %s, %s);",
    #     ('testuser', 'test@example.com', 'hashed_pw')
    # )
    fake_cursor.execute.assert_any_call('select userId from auth where userName= %s', ('testuser',))
    fake_cursor.execute.assert_any_call(
        '''insert into users(userId, firstName, secondName, age, gender, status, phoneNumber)
    values (%s, %s, %s, %s, %s, %s, %s);''',
        (42, 'John', 'Doe', 30, 'Male', 'active', '+71234567890')
    )
    fake_conn.commit.assert_called()

def test_login_success(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.side_effect = [(42,), ("hashed-password",)]
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    monkeypatch.setattr('UserService.app.users.connection', fake_conn)
    monkeypatch.setattr('UserService.app.users.verifyPW', lambda plain, hashed: True)
    monkeypatch.setattr('UserService.app.users.createToken', lambda data: "fake-token")

    data = {"userName": "testuser", "password": "pass123r4r34rrer"}
    response = client.post("/login", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["access_token"] == "fake-token"
    assert result["refresh_token"] is None
    assert result["user_id"] == 42

@freeze_time("2025-01-01 12:00:00")
def test_update_profile(monkeypatch):
    fake_cursor = MagicMock()
    fixed_time = datetime(2025, 1, 1, 12, 0, 0)
    fake_cursor.fetchone.return_value = (fixed_time,)
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    monkeypatch.setattr('UserService.app.users.connection', fake_conn)
    monkeypatch.setattr('UserService.app.users.validateToken', lambda token: 42)

    data = {
        "token": "dummy", 
        "firstName": "Jane",
        "secondName": "Doe",
        "age": 25,
        "gender": "Female",
        "status": "active",
        "phoneNumber": "+70987654321"
    }
    response = client.put("/profile", json=data)
    assert response.status_code == 200
    assert response.json() == {"message": "Profile updated"}
    fake_cursor.execute.assert_any_call(
        '''update users set firstName = %s, secondName = %s,
     age = %s, gender = %s, status = %s, phoneNumber = %s, lastUpdate = %s where userID= %s''',
        ('Jane', 'Doe', 25, 'Female', 'active', '+70987654321', fixed_time, 42)
    )
    fake_cursor.execute.assert_any_call('select lastUpdate from users where userID= %s', (42,))
    fake_conn.commit.assert_called()

def test_process_message_post_viewed(monkeypatch):
    dummy_client = MagicMock()
    monkeypatch.setattr(consumer, 'client', dummy_client)

    event_data = {"timestamp": "2025-01-01T12:00:00", "post_id": "123", "user_id": "user_1"}
    message = DummyMessage(topic="post_viewed", value_bytes=json.dumps(event_data).encode('utf-8'))

    consumer.process_message(message.topic(), message)

    dummy_client.command.assert_called_once_with("""
        insert into views (timestamp, postId, userId) values (%(timestamp)s, %(post_id)s, %(user_id)s)
    """, parameters=event_data
    )

def test_process_message_post_liked(monkeypatch):
    dummy_client = MagicMock()
    monkeypatch.setattr(consumer, 'client', dummy_client)

    event_data = {"timestamp": "2025-01-02T13:00:00", "post_id": "456", "user_id": "user_2"}
    message = DummyMessage(topic="post_liked", value_bytes=json.dumps(event_data).encode('utf-8'))

    consumer.process_message(message.topic(), message)

    dummy_client.command.assert_called_once_with("""
        insert into likes (timestamp, postId, userId) values (%(timestamp)s, %(post_id)s, %(user_id)s)
    """, parameters=event_data
    )

@pytest.fixture(autouse=True)
def mock_grpc_services(mocker):
    mocker.patch('APIGateway.main.get_grpc', return_value=MagicMock())
    mocker.patch('APIGateway.main.get_grpc_stat', return_value=MagicMock())
    
    mocker.patch('requests.post')
    mocker.patch('requests.put')
    mocker.patch('requests.get')


@pytest.fixture
def auth_client():
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'user_id': 1
        }
        
        response = client.post(
            "/login",
            json={"mail": "test@test.com", "password": "password11213313"}
        )
        assert response.status_code == 200
        return client1

def test_user_lifecycle(auth_client, mocker):
    mock_post = mocker.patch('requests.post')
    mock_put = mocker.patch('requests.put')
    mock_get = mocker.patch('requests.get')
    
    mock_post.return_value.json.return_value = {"status": "user created"}
    register_data = {
        "firstName": "Иван",
        "secondName": "Иванов",
        "userName": "ivanov",
        "mail": "ivan@example.com",
        "password": "strongpassword123",
        "age": 25,
        "gender": "Male",
        "status": "Активный пользователь",
        "phoneNumber": "+71234567890"
    }
    response = auth_client.post("/register", json=register_data)
    assert response.status_code == 200
    assert response.json()["status"] == "user created"
    
    mock_post.return_value.json.return_value = {
        'access_token': 'test_token',
        'user_id': '1'
    }
    response = auth_client.post(
        "/login",
        json={"userName": "ivanov", "password": "strongpassword123"}
    )
    assert response.status_code == 200
    assert 'access_token' in response.cookies
    
    mock_put.return_value.json.return_value = {"status": "profile updated"}
    update_data = {
        "firstName": "Иван",
        "secondName": "Петров",
        "age": 26,
        "gender": "Male",
        "status": "Премиум пользователь",
        "phoneNumber": "+71234567891"
    }
    response = auth_client.put("/profile", json=update_data)
    assert response.status_code == 200
    assert response.json()["status"] == "profile updated"
    
    mock_get.return_value.json.return_value = {
        "id": 1,
        "firstName": "Иван",
        "secondName": "Петров",
        "userName": "ivanov",
        "mail": "ivan@example.com",
        "age": 26,
        "gender": "Male",
        "status": "Премиум пользователь",
        "phoneNumber": "+71234567891"
    }
    response = auth_client.get("/profile")
    assert response.status_code == 200
    profile = response.json()
    assert profile["secondName"] == "Петров"
    assert profile["age"] == 26
    
    response = auth_client.post("/logout")
    assert response.status_code == 200
    assert 'access_token' not in response.cookies

def test_post_creation_and_interaction(auth_client, mocker):
    post_stub = mocker.patch('main.get_grpc').return_value
    stat_stub = mocker.patch('main.get_grpc_stat').return_value
    
    post_stub.CreatePost.return_value = pcsev_pb2.CreatePostResponse(
        postId=1,
        title="Мой первый пост",
        description="Это тестовый пост для проверки функционала",
        userId=1,
        created_at=Timestamp(seconds=1630000000),
        updated_at=Timestamp(seconds=1630000000),
        isPrivate=False,
        tags=["test", "python"]
    )
    
    response = auth_client.post(
        "/posts",
        json={
            "title": "Мой первый пост",
            "description": "Это тестовый пост для проверки функционала",
            "isPrivate": False,
            "tags": ["test", "python"]
        }
    )
    assert response.status_code == 200
    post = response.json()
    assert post["title"] == "Мой первый пост"
    assert "python" in post["tags"]
    
    post_stub.LikePost.return_value = pcsev_pb2.LikePostResponse(
        likeId=1,
        userId=1,
        postId=1,
        added_at=Timestamp(seconds=1630000001)
    )
    
    response = auth_client.post("/posts/1/like")
    assert response.status_code == 200
    assert response.json()["likeId"] == 1
    
    post_stub.CommentPost.return_value = pcsev_pb2.CommentPostResponse(
        commentId=1,
        postId=1,
        userId=1,
        text="Отличный пост!",
        created_at=Timestamp(seconds=1630000002)
    )
    
    response = auth_client.post(
        "/posts/1/comment",
        params={"text": "Отличный пост!"}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Отличный пост!"
    
    stat_stub.GetPostStats.return_value = stat_pb2.PostStatsResponse(
        views=15,
        likes=3,
        comments=2
    )
    
    response = auth_client.get("/stats/1")
    assert response.status_code == 200
    stats = response.json()
    assert stats["likes"] == 3
    assert stats["comments"] == 2
    
    stat_stub.GetPostLikesByDay.return_value = stat_pb2.LikesByDayResponse(
        stats=[stat_pb2.DayStats(date="2023-01-01", count=2)]
    )
    
    response = auth_client.get("/stats/1/likes")
    assert response.status_code == 200
    assert response.json()["stats"][0]["date"] == "2023-01-01"

def test_content_management_and_analytics(auth_client, mocker):
    post_stub = mocker.patch('main.get_grpc').return_value
    stat_stub = mocker.patch('main.get_grpc_stat').return_value
    
    posts = [
        {
            "id": 1,
            "title": "Пост про Python",
            "tags": ["python", "programming"]
        },
        {
            "id": 2,
            "title": "Пост про FastAPI",
            "tags": ["fastapi", "web"]
        }
    ]
    
    for post in posts:
        post_stub.CreatePost.return_value = pcsev_pb2.CreatePostResponse(
            postId=post["id"],
            title=post["title"],
            description=f"Описание {post['title']}",
            userId=1,
            tags=post["tags"]
        )
        response = auth_client.post(
            "/posts",
            json={
                "title": post["title"],
                "description": f"Описание {post['title']}",
                "isPrivate": False,
                "tags": post["tags"]
            }
        )
        assert response.status_code == 200
    
    post_stub.UpdatePost.return_value = pcsev_pb2.UpdatePostResponse(
        postId=1,
        title="Обновленный пост про Python",
        description="Новое описание",
        tags=["python", "backend"]
    )
    
    response = auth_client.put(
        "/posts/1",
        json={
            "title": "Обновленный пост про Python",
            "description": "Новое описание",
            "isPrivate": False,
            "tags": ["python", "backend"]
        }
    )
    assert response.status_code == 200
    assert "backend" in response.json()["tags"]
    
    mock_posts = [
        pcsev_pb2.PostResponse(
            postId=1,
            title="Обновленный пост про Python",
            tags=["python", "backend"]
        ),
        pcsev_pb2.PostResponse(
            postId=2,
            title="Пост про FastAPI",
            tags=["fastapi", "web"]
        )
    ]
    post_stub.ListPosts.return_value = pcsev_pb2.ListPostsResponse(posts=mock_posts)
    
    response = auth_client.get("/posts?offset=0&limit=10")
    assert response.status_code == 200
    posts = response.json()["posts"]
    assert len(posts) == 2
    assert posts[0]["title"] == "Обновленный пост про Python"
    
    post_stub.DeletePost.return_value = pcsev_pb2.DeletePostResponse(
        success=True,
        postId=2
    )
    
    response = auth_client.delete("/posts/2")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    stat_stub.GetTopPostsByMetric.return_value = stat_pb2.TopPostsResponse(
        posts=[stat_pb2.PostStats(postId=1, count=100)]
    )
    
    response = auth_client.get("/stats/views/top-posts")
    assert response.status_code == 200
    top_posts = response.json()["posts"]
    assert top_posts[0]["postId"] == 1
    assert top_posts[0]["count"] == 100
