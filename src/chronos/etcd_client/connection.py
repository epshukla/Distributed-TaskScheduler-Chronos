from etcd3 import Client as Etcd3Client


def create_etcd_client(host: str = "localhost", port: int = 2379) -> Etcd3Client:
    return Etcd3Client(host=host, port=port)
