import re
import select
import socket


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


def handle_request(data):
  ascii_request = b''.join(data).decode(encoding="us-ascii")
  for request in REQUEST_LINE_FORMAT.finditer(ascii_request):
    print(dict(
      verb=request['verb'],
      url=request['url'],
      version=request['version'],
      headers=parse_headers(request['headers']),
    ))


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
            handle_request(connected_clients[client])

      for client in unusual:
        print(f'closed connection to {pretty_print_socket(new_connection)}')
        client.shutdown(socket.SHUT_RDRW)
        client.close()
        del connected_clients[client]
  

if __name__ == '__main__':
  run()
