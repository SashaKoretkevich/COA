import grpc
import time
from concurrent import futures
from protos import pcsev_pb2
from protosimport pcsev_pb2_grpc
from grpcSev import PostService


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pcsev_pb2_grpc.add_PostServiceServicer_to_server(PostService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC запущен на порту 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    main()
