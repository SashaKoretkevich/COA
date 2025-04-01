from fastapi import FastAPI, Response, Request,  HTTPException
from models import userCreate, userLogin, userUpdate, postCreate
from protos import pcsev_pb2
from protos import pcsev_pb2_grpc
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


api = FastAPI()

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

@api.post("/posts/")
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
        return {"postId": response.postId}
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
            "creationTime": response.creationTime,
            "lastUpdate": response.lastUpdate,
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
            "creationTime": response.creationTime,
            "lastUpdate": response.lastUpdate,
            "isPrivate": response.isPrivate,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/posts/")
def listPosts(request: Request, offset: int, limit: int):
    conn = get_grpc()
    userID = request.cookies.get('user_id')
    if not userID:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    userID = int(userID)
    response = conn.ListPosts(pcsev_pb2.ListPostsRequest(offset=offset, limit=limit, userId = userID))
    try:
        return {"posts": [
            {
                "postId": post.postId,
                "title": post.title,
                "description": post.description,
                "userId": post.userId,
                "creationTime": post.creationTime,
                "lastUpdate": post.lastUpdate,
                "isPrivate": post.isPrivate,
                "tags": list(post.tags)
            } for post in response.posts
        ]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

