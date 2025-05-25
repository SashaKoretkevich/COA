from fastapi import FastAPI, HTTPException, APIRouter, Response, Request
from models import userCreate, userLogin, userUpdate, postCreate
from protos  import pcsev_pb2
from protos  import pcsev_pb2_grpc
from protos import stat_pb2
from protos  import stat_pb2_grpc
import requests
import json
import os
import grpc
from dotenv import load_dotenv, dotenv_values 

GRPC_TO_HTTP = {
    grpc.StatusCode.OK: 200,
    grpc.StatusCode.CANCELLED: 499,
    grpc.StatusCode.UNKNOWN: 500,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.UNAUTHENTICATED: 401,
    grpc.StatusCode.RESOURCE_EXHAUSTED: 429,
    grpc.StatusCode.FAILED_PRECONDITION: 400,
    grpc.StatusCode.ABORTED: 409,
    grpc.StatusCode.OUT_OF_RANGE: 400,
    grpc.StatusCode.UNIMPLEMENTED: 501,
    grpc.StatusCode.INTERNAL: 500,
    grpc.StatusCode.UNAVAILABLE: 503,
    grpc.StatusCode.DATA_LOSS: 500,
}


load_dotenv() 


url = os.environ.get('USER_SERVICE')


def get_grpc():
    channel = grpc.insecure_channel(os.environ.get('POST_SERVICE'))
    return pcsev_pb2_grpc.PostServiceStub(channel)

def get_grpc_stat():
    channel = grpc.insecure_channel(os.environ.get('STATISTICS_SERVICE'))
    return stat_pb2_grpc.StatisticsServiceStub(channel)

api = APIRouter()

@api.post("/register")
def register(user: userCreate):
    response = requests.post(f"{url}register", json=user.model_dump())
    return response.json()

@api.post("/login")
def login(response: Response, user: userLogin):
    responseData = requests.post(f"{url}login", json=user.model_dump()).json()
    if not responseData['access_token']:
        raise HTTPException(status_code=400, detail="Неправильные данные")
    response.set_cookie(key="access_token", value=responseData['access_token'], httponly=True)
    response.set_cookie(key="user_id", value=responseData['user_id'], httponly=True)
    return responseData

@api.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="user_id")
    return {'message': 'Пользователь вышел из системы'}

@api.put("/profile")
def updateProfile(request: Request, user_data: userUpdate):
    token = request.cookies.get('access_token')
    user_data.token = token
    if not token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    response = requests.put(f"{url}profile", json=user_data.model_dump())
    return response.json()

@api.get("/profile")
def getUser(request: Request):
    send = {}
    send['token'] = request.cookies.get('access_token')
    if not request.cookies.get('access_token'):
        raise HTTPException(status_code=404, detail="Токен не найден")
    response = requests.get(f"{url}profile", json = send)
    return response.json()

@api.post("/posts")
def createPost(request: Request,post: postCreate):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.CreatePost(pcsev_pb2.CreatePostRequest(
            title=post.title,
            description=post.description,
            userId=userID,
            isPrivate=post.isPrivate,
            tags=post.tags
        ))
        return {
            "postId": response.postId,
            "title": response.title,
            "description": response.description,
            "userId": response.userId,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "isPrivate": response.isPrivate,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/posts/{post_id}")
def getPost(request: Request, post_id: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.GetPost(pcsev_pb2.GetPostRequest(postId=post_id, userId = userID))
        return {
            "postId": response.postId,
            "title": response.title,
            "description": response.description,
            "userId": response.userId,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "isPrivate": response.isPrivate,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.delete("/posts/{post_id}")
def deletePost(request: Request, post_id: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.DeletePost(pcsev_pb2.DeletePostRequest(postId=post_id, userId=userID))
        return {
            "success": response.success,
            "postId": response.postId
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.put("/posts/{post_id}")
def updatePost(request: Request, post_id: int, post: postCreate):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.UpdatePost(pcsev_pb2.UpdatePostRequest(
            postId=post_id,
            title=post.title,
            description=post.description,
            userId = userID,
            isPrivate=post.isPrivate,
            tags=post.tags
        ))
        return {
            "postId": response.postId,
            "title": response.title,
            "description": response.description,
            "userId": response.userId,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "isPrivate": response.isPrivate,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/posts")
def listPosts(request: Request, offset: int, limit: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.ListPosts(pcsev_pb2.ListPostsRequest(offset=offset, limit=limit, userId = userID))
        return {"posts": [
            {
                "postId": post.postId,
                "title": post.title,
                "description": post.description,
                "userId": post.userId,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "isPrivate": post.isPrivate,
                "tags": list(post.tags)
            } for post in response.posts
        ]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/posts/{post_id}/comment")
def listComments(request: Request, post_id: int, offset: int, limit: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    try:
        response = conn.ListComments(pcsev_pb2.ListCommentsRequest(offset=offset, limit=limit, userId = userID, postId = post_id))
        return {"comments": [
            {
                "commentId": comment.commentId,
                "postId": comment.postId,
                "userId": comment.userId,
                "text": comment.text,
                "created_at": comment.created_at
            } for comment in response.comments
        ]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())
    
@api.get("/posts/{post_id}/view")
def viewPost(request: Request, post_id: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userId = int(userID)
    try:
        response = conn.ViewPost(pcsev_pb2.ViewPostRequest(postId=post_id, userId = userId))
        return {
            "postId": response.postId,
            "title": response.title,
            "description": response.description,
            "userId": response.userId,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "isPrivate": response.isPrivate,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.post("/posts/{post_id}/like")
def likePost(request: Request, post_id: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userId = int(userID)
    try:
        response = conn.LikePost(pcsev_pb2.LikePostRequest(postId=post_id, userId=userId))
        return {
            "likeId": response.likeId,
            "userId": response.userId,
            "postId": response.postId,
            "added_at": response.added_at,
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.post("/posts/{post_id}/comment")
def commentPost(request: Request, post_id: int, text: str):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userId = int(userID)
    try:
        response = conn.CommentPost(pcsev_pb2.CommentPostRequest(
            postId=post_id,
            userId=userId,
            text=text
        ))
        return {
            "commentId": response.commentId,
            "postId": response.postId,
            "userId": response.userId,
            "text": response.text,
            "created_at": response.created_at,
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/stats/{post_id}")
def getPostStats(request: Request, post_id : int):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetPostStats(stat_pb2.PostRequest(postId=post_id))
        return {
            "views": response.views,
            "likes": response.likes,
            "comments": response.comments
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


@api.get("/stats/{post_id}/views")
def getPostViewsByDay(request: Request, post_id : int):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetPostViewsByDay(stat_pb2.PostRequest(postId=post_id))
        return {"stats": [{"date": stat.date, "count": stat.count} for stat in response.stats]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


@api.get("/stats/{post_id}/likes")
def GetPostLikesByDay(request: Request, post_id: int):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetPostLikesByDay(stat_pb2.PostRequest(postId=post_id))
        return {"stats": [{"date": stat.date, "count": stat.count} for stat in response.stats]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


@api.get("/stats/{post_id}/comments")
def getPostCommentsByDay(request: Request, post_id : int):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetPostCommentsByDay(stat_pb2.PostRequest(postId=post_id))
        return {"stats": [{"date": stat.date, "count": stat.count} for stat in response.stats]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


@api.get("/stats/{metric}/top-posts")
def getTopPosts(request: Request, metric : str):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetTopPostsByMetric(stat_pb2.MetricRequest(metric=metric))
        return {"posts": [{"postId": post.postId, "count": post.count} for post in response.posts]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


@api.get("/stats/{metric}/top-users")
def getTopUsers(request: Request, metric : str):
    stub = get_grpc_stat()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    try:
        response = stub.GetTopUsersByMetric(stat_pb2.MetricRequest(metric=metric))
        return {"users": [{"userId": user.userId, "count": user.count} for user in response.users]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


