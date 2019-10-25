import socket


def run(port=80):
  with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as s:
    s.bind(('', port))
    s.listen()

    while True:
      conn, address = s.accept()
      print(conn.recv(4096))
      conn.close()
  

if __name__ == '__main__':
  run()
