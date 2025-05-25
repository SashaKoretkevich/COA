import grpc
from protosimport pcsev_pb2
from protos import pcsev_pb2_grpc
from kafkaProducer import KafkaProducer
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv() 

def dbConn():
    return psycopg2.connect(database=os.getenv("DBNAME1"), user=os.getenv("USER1"), 
                        password=os.getenv("PASSWORD1"), port=os.getenv("PORT1"), host=os.getenv("HOST1"))

kafka_producer = KafkaProducer()

class PostService(pcsev_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("insert into posts (title, description, userid, created_at, isPrivate, tags) values (%s, %s, %s, now(), %s, %s) returning postId;", (request.title, request.description, request.userId, request.isPrivate, "{" + ",".join([f'"{tag}"' for tag in request.tags]) + "}" ))
        conn.commit()
        postId =cur.fetchone()[0]

        cur.execute("select * from posts where postid = %s and deleted_at is null;", (postId,))
        post =cur.fetchone()
        cur.close()
        conn.close()
        return pcsev_pb2.CreatePostResponse(
            postId=post[0],
            title=post[1],
            description=post[2],
            userId=post[3],
            created_at=str(post[4]),
            updated_at=str(post[5]),
            isPrivate=post[7],
            tags=post[8]
        )

    def GetPost(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        cur.close()
        conn.close()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[7] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        return pcsev_pb2.GetPostResponse(
            postId=post[0],
            title=post[1],
            description=post[2],
            userId=post[3],
            created_at=str(post[4]),
            updated_at=str(post[5]),
            isPrivate=post[7],
            tags=post[8]
        )

    def UpdatePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден1")
        if post[3] != request.userId:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        cur.execute("update posts set title = %s, description = %s, updated_at = now(), isPrivate = %s, tags = %s where postid = %s and deleted_at is null;", (request.title, request.description, request.isPrivate, "{" + ",".join([f'"{tag}"' for tag in request.tags]) + "}", request.postId))
        conn.commit()
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
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
            created_at=str(postUpdate[4]),
            updated_at=str(postUpdate[5]),
            isPrivate=postUpdate[7],
            tags=postUpdate[8]
        )

    def DeletePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor()
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId, ))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[3] != request.userId:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        print(f"Deleting post with ID: {request.postId}")
        cur.execute("update posts set deleted_at = current_timestamp where postid = %s returning postid;", (request.postId, ))
        postDel =cur.fetchone()
        conn.commit()

        cur.execute("select exists (select 1 from likes where postid = %s and deleted_at is null);", (request.postId, ))
        likes = cur.fetchone()[0]
        if likes:
            cur.execute("update likes set deleted_at = current_timestamp where postid = %s;", (request.postId, ))
            conn.commit()

        cur.execute("select exists (select 1 from comments where postid = %s and deleted_at is null);", (request.postId, ))
        comments = cur.fetchone()[0]
        if comments:
            cur.execute("update comments set deleted_at = current_timestamp where postid = %s;", (request.postId, ))
            conn.commit()
        cur.close()
        conn.close()

        if not postDel:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не был удален")
        return pcsev_pb2.DeletePostResponse(success=True, postId = postDel[0])

    def ListPosts(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("select * from posts where deleted_at is null and (isPrivate = false or userid = %s) limit %s offset %s;", (request.userId, request.limit, request.offset))
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
                    created_at=str(post[4]),
                    updated_at=str(post[5]),
                    isPrivate=post[7],
                    tags=post[8])
                for post in posts
            ]
        )
    
    def ListComments(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[7] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        cur.execute("select * from comments where deleted_at is null and postid = %s limit %s offset %s;", (request.postId, request.limit, request.offset))
        comments =cur.fetchall()
        cur.close()
        conn.close()
        return pcsev_pb2.ListCommentsResponse(
            comments=[
                pcsev_pb2.Comment(
                    commentId=comment[0],
                    postId=comment[1],
                    userId=comment[2],
                    text=comment[3],
                    created_at=str(comment[4]),)
                for comment in comments
            ]
        )


    def ViewPost(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        cur.close()
        conn.close()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[7] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        kafka_producer.send_post_viewed_event(request.userId, post[0])
        return pcsev_pb2.ViewPostResponse(
            postId=post[0],
            title=post[1],
            description=post[2],
            userId=post[3],
            created_at=str(post[4]),
            updated_at=str(post[5]),
            isPrivate=post[7],
            tags=post[8]
        )

    def LikePost(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[7] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")

        cur.execute("select exists (select 1 from likes where postid = %s and userid = %s and deleted_at is null);", (request.postId, request.userId))
        like =cur.fetchone()[0]
        if like:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "Лайк уже существует")
        else:
            cur.execute("insert into likes (userid, postid) values (%s, %s) returning likeid;", (request.userId, request.postId))
        conn.commit()
        likeId =cur.fetchone()[0]
        if not likeId:
            context.abort(grpc.StatusCode.NOT_FOUND, "Лайк не был добавлен")
        cur.execute("select * from likes where likeid = %s and deleted_at is null;", (likeId,))
        like =cur.fetchone()
        cur.close()
        conn.close()
        kafka_producer.send_post_liked_event(request.userId, like[2])
        return pcsev_pb2.LikePostResponse(likeId=like[0], userId = like[1], postId=like[2], added_at=str(like[3]))

    def CommentPost(self, request, context):
        conn = dbConn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from posts where postid = %s and deleted_at is null;", (request.postId,))
        post =cur.fetchone()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post[7] == True:
            if post[3] != request.userId:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")

        cur.execute("insert into comments (postid, userid, text) values (%s, %s, %s) returning commentId;", (request.postId, request.userId, request.text))
        conn.commit()
        commentId =cur.fetchone()[0]
        cur.execute("select * from comments where commentid = %s and deleted_at is null;", (commentId,))
        comment =cur.fetchone()
        if not comment:
            context.abort(grpc.StatusCode.NOT_FOUND, "Комментарий не был добавлен")
        cur.close()
        conn.close()
        kafka_producer.send_post_comment_event(request.userId, comment[1])
        return pcsev_pb2.CommentPostResponse(commentId=comment[0], postId = comment[1], userId=comment[2], text =comment[3], created_at=str(comment[4]))