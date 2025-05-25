import grpc
import time
import threading
from concurrent import futures
import stat_pb2
import stat_pb2_grpc
from grpcSev import StatisticsService
from kafkaConsumer import start_kafka_consumer

def main():
    kafka_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    kafka_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    stat_pb2_grpc.add_StatisticsServiceServicer_to_server(StatisticsService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("gRPC запущен на порту 50052...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("gRPC остановлен")
        server.stop(0)

if __name__ == '__main__':
    main()