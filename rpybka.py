import select
import socket


def pretty_print_socket(connection):
  assert(connection)
  ip_address, port = connection.getpeername()
  return f'<{ip_address}:{port}>'


def run(port=80):
  connected_clients = {}

  with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', port))
    server.listen()

    while True:
      read_ready = [server] + list(connected_clients.keys())
      readable, _, unusual = select.select(read_ready, [], read_ready, 1)

      for client in readable:
        if client is server:
          new_connection, address = server.accept()
          new_connection.setblocking(False)
          connected_clients[new_connection] = []
          print(f'client connected from {pretty_print_socket(new_connection)}')
        else:
          data = client.recv(4096)
          if data:
            connected_clients[client].append(data)
            print(f'received data from {pretty_print_socket(new_connection)}: {data!s}')

      for client in unusual:
        print(f'closed connection to {pretty_print_socket(new_connection)}')
        client.shutdown(socket.SHUT_RDRW)
        client.close()
        del connected_clients[client]
  

if __name__ == '__main__':
  run()
