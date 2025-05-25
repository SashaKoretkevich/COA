import grpc
from protos import stat_pb2
from protos import stat_pb2_grpc
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import os
import clickhouse_connect


load_dotenv() 

client = clickhouse_connect.get_client(
    host=os.getenv("DBNAME2"),
    port=os.getenv("PORT2"),
    username=os.getenv("USER2"),
    password=os.getenv("PASSWORD2")
)

class StatisticsService(stat_pb2_grpc.StatisticsServiceServicer):
    def GetPostStats(self, request, context):
        postId = request.postId
        views = client.query(f"select count() from views where postId = '{postId}'").result_rows[0][0]
        likes = client.query(f"select count() from likes where postId = '{postId}'").result_rows[0][0]
        comments = client.query(f"select count() from comments where postId = '{postId}'").result_rows[0][0]
        return stat_pb2.PostStatsResponse(views=views, likes=likes, comments=comments)

    def GetPostViewsByDay(self, request, context):
        return self._get_timeline("views", request.postId)

    def GetPostLikesByDay(self, request, context):
        return self._get_timeline("likes", request.postId)

    def GetPostCommentsByDay(self, request, context):
        return self._get_timeline("comments", request.postId)

    def _get_timeline(self, table, postId):
        rows = client.query(
            f"""select toDate(timestamp) as date, count() as cnt from {table} where postId = '{postId}'group by date order by date""").named_results()
        return stat_pb2.StatsByDayResponse (
            stats =[stat_pb2.DailyStatsItem(date=str(row['date']), count=row['cnt']) for row in rows]
        )

    def GetTopPostsByMetric(self, request, context):
        table = request.metric 
        rows = client.query(f"""select postId, count() as cnt from {table} group by postId order by cnt desc limit 10""").named_results()
        return stat_pb2.TopPostsResponse(
            posts=[stat_pb2.TopPost(postId=row['postId'], count=row['cnt']) for row in rows]
        )

    def GetTopUsersByMetric(self, request, context):
        table = request.metric
        rows = client.query(f"""select userId, count() as cnt from {table} group by userId order by cnt desc limit 10""").named_results()
        return stat_pb2.TopUsersResponse(
            users=[stat_pb2.TopUser(userId=row['userId'], count=row['cnt']) for row in rows]
        )