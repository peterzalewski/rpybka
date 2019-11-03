import re
import select
import socket as lib_socket


REQUEST_LINE_FORMAT = re.compile(
  r"""
  (?P<verb>GET|HEAD|POST|PUT|DELETE|DELETE|CONNECT|OPTIONS|TRACE)
  [ ]
  (?P<url>\S+)
  [ ]
  HTTP/(?P<version>1\.[01])
  \r\n
  (?P<headers>
    (?:
      [-a-zA-Z]+:.+\r\n
    )*?
  )
  \r\n
  """,
  flags=re.VERBOSE,
)

HEADER_FORMAT = re.compile(
  r"""
  (?P<field_name>[-a-zA-Z]+)
  :
  [ \t]*
  (?P<field_value>[\x21-\x7E]+)  # All visible US-ASCII characters
  [ \t]*
  \r\n
  """,
  flags=re.VERBOSE,
)

def parse_headers(headers):
  return {
    header.group('field_name'): header.group('field_value')
    for header in HEADER_FORMAT.finditer(headers)
  }


def handle_request(client):
  ascii_request = client.incoming
  for request in REQUEST_LINE_FORMAT.finditer(ascii_request):
    print(dict(
      verb=request['verb'],
      url=request['url'],
      version=request['version'],
      headers=parse_headers(request['headers']),
    ))
    client.send('HTTP/1.1 200 OK\r\nConnection: Close\r\n\r\n')


class ConnectedClient(object):
  def __init__(self, socket, address):
    super().__init__()
    self.socket = socket
    self.address, self.port = address
    self.incoming = ''
    self._outgoing = bytearray()

  def receive(self, data):
    ascii_data = data.decode(encoding="us-ascii")
    self.incoming += ascii_data

  def send(self, data):
    ascii_data = data.encode(encoding="us-ascii")
    self._outgoing += ascii_data

  def ready_to_send(self):
    return len(self._outgoing) > 0

  def __repr__(self):
    return f'<{self.address}:{self.port}>'


def run(port=80):
  connected_clients = {}

  with lib_socket.socket(family=lib_socket.AF_INET, type=lib_socket.SOCK_STREAM) as server:
    server.setsockopt(lib_socket.SOL_SOCKET, lib_socket.SO_REUSEADDR, 1)
    server.bind(('', port))
    server.listen(0xffff)

    while True:
      # TODO: Rewrite with kqueue
      connected_sockets = set([server] + list(connected_clients.keys()))
      readable, writable, unusual = select.select(connected_sockets, connected_sockets, connected_sockets, 1)

      for socket in readable:
        if socket is server:
          new_connection, address = server.accept()
          new_connection.setblocking(False)
          connected_clients[new_connection] = ConnectedClient(new_connection, address)
          print(f'client connected from {connected_clients[new_connection]!r}')
        else:
          data = socket.recv(4096)
          if data:
            connected_clients[socket].receive(data)
            # TODO: This naively loops over every request from the same socket.
            handle_request(connected_clients[socket])

      for socket in writable:
        if socket is server:
          continue
        client = connected_clients[socket]
        if client.ready_to_send():
          send_start = 0
          while send_start < len(client._outgoing):
            send_size = min(4096, len(client._outgoing) - send_start)
            socket.sendmsg([client._outgoing[send_start:send_start + send_size]])
            send_start += send_size
          del client._outgoing[:send_start]
        socket.close()
        del connected_clients[socket]

      for socket in unusual:
        print(f'closed connection to {connected_clients[socket]!r}')
        socket.shutdown(lib_socket.SHUT_RDRW)
        socket.close()
        del connected_clients[socket]
  

if __name__ == '__main__':
  run()
