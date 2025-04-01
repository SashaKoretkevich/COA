import grpc
from protosimport pcsev_pb2
from protos import pcsev_pb2_grpc
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv() 

def dbConn():
    return psycopg2.connect(database=os.getenv("DBNAME1"), user=os.getenv("USER1"), 
                        password=os.getenv("PASSWORD1"), port=os.getenv("PORT1"), host=os.getenv("HOST1"))

class PostService(pcsev_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("insert into posts (title, description, userId, creationTime, lastUpdate, isPrivate, tags) values (%s, %s, %s, now(), now(), %s, %s) returning postId;", (request.title, request.description, request.userId, request.isPrivate, "{" + ",".join([f'"{tag}"' for tag in request.tags]) + "}" ))
        postId =cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return pcsev_pb2.CreatePostResponse(postId=postId)

    def GetPost(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postId = %s;", (request.postId,))
        post =cur.fetchone()
        cur.close()
        conn.close()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[6] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        return pcsev_pb2.GetPostResponse(
            postId=post[0],
            title=post[1],
            description=post[2],
            userId=post[3],
            creationTime=str(post[4]),
            lastUpdate=str(post[5]),
            isPrivate=post[6],
            tags=post[7]
        )

    def UpdatePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("select * from posts where postId = %s;", (request.postId,))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден1")
        if post[3] != request.userId:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        cur.execute("update posts set title = %s, description = %s, lastUpdate = now(), isPrivate = %s, tags = %s where postId = %s;", (request.title, request.description, request.isPrivate, "{" + ",".join([f'"{tag}"' for tag in request.tags]) + "}", request.postId))
        conn.commit()
        cur.execute("select * from posts where postId = %s;", (request.postId,))
        postUpdate =cur.fetchone()
        time = datetime.utcnow()
        if postUpdate[5] == time:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не был обновлен")
        cur.close()
        conn.close()
        return pcsev_pb2.UpdatePostResponse(
            postId=postUpdate[0],
            title=postUpdate[1],
            description=postUpdate[2],
            userId=postUpdate[3],
            creationTime=str(postUpdate[4]),
            lastUpdate=str(postUpdate[5]),
            isPrivate=postUpdate[6],
            tags=postUpdate[7]
        )

    def DeletePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("select * from posts where postId = %s;", (request.postId, ))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[3] != request.userId:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        print(f"Deleting post with ID: {request.postId}")
        cur.execute("delete from posts where postId = %s returning postId;", (request.postId, ))
        postDel =cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if not postDel:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не был удален")
        return pcsev_pb2.DeletePostResponse(success=True, postId = postDel[0])

    def ListPosts(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where isPrivate = false or userId = %s limit %s offset %s;", (request.userId, request.limit, request.offset))
        posts =cur.fetchall()
        cur.close()
        conn.close()
        return pcsev_pb2.ListPostsResponse(
            posts=[
                pcsev_pb2.GetPostResponse(
                    postId=post[0],
                    title=post[1],
                    description=post[2],
                    userId=post[3],
                    creationTime=str(post[4]),
                    lastUpdate=str(post[5]),
                    isPrivate=post[6],
                    tags=post[7])
                for post in posts
            ]
        )