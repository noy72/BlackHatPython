import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)

print(f"[*] Listening on {bind_ip}:{bind_port}")


def handle_client(client_socket):
    # クライアントが送信してきたデータを表示
    request = client_socket.recv(1024)
    print(f"[*] Received: {request}")

    # パケットの返送
    client_socket.send(b"ACK!")
    client_socket.close()


while True:
    client, addr = server.accept()
    print(f"[*] Accepted connection from: {addr[0]}:{addr[1]}")

    # 受信データを処理するスレッドの軌道
    client_hander = threading.Thread(target=handle_client, args=(client,))
    client_hander.start()
