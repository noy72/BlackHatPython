import socket

# target_host = "www.google.com"
# target_port = 80
target_host = "0.0.0.0"
target_port = 9999

# ソケットオブジェクトの作成
# AF_INET       : 標準的なIPv4のアドレスやホスト名を使用する設定
# SOCK_STREAM   : tcpを用いる設定
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((target_host, target_port))
client.send(b"TCP client")
# client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# Accept data
response = client.recv(4096)
print(response)
