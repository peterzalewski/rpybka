import select
import socket


def receive_all(conn, receive_size=4096, timeout=1):
  message = []
  while True:
    ready, _, _ = select.select([conn], [], [], timeout)
    if not ready:
      break
    data = ready[0].recv(receive_size)
    message.append(data)

  return b''.join(message)


def run(port=80):
  with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as s:
    s.bind(('', port))
    s.listen()

    while True:
      try:
        conn, address = s.accept()
      except KeyboardInterrupt:
        break

      try:
        request = receive_all(conn)
        print(request)
      finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
  

if __name__ == '__main__':
  run()
