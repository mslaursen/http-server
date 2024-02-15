import socket


HOST, PORT = "", 4221
listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)

print("Serving HTTP on port %s ..." % PORT)


def parse_request(request: bytes) -> str:

    text = request.decode()
    path = text.split("\r\n")[0].split()[1]

    response_status = ""

    match path:
        case "/":
            response_status = "200 OK"
        case _:
            response_status = "404 Not Found"

    return response_status


while True:
    client_connection, client_address = listen_socket.accept()

    request = client_connection.recv(1024)

    text = request.decode()
    path = text.split("\r\n")[0].split()[1]

    response_status = parse_request(request)

    http_response = f"HTTP/1.1 {response_status}\r\n\r\n"

    client_connection.sendall(http_response.encode("utf-8"))
    client_connection.close()
