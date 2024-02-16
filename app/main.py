import socket


def main() -> None:

    HOST, PORT = "", 4221
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(1)

    HTTP_VERSION = "HTTP/1.1"
    CRLF = "\r\n"
    HTTP_LB = CRLF * 2
    BUFFER_SIZE = 1024

    print(f"Serving HTTP on port {PORT}")

    def parse_request_line(request: bytes) -> tuple[str, str, str]:
        request_line = request.decode().split(CRLF)[0]
        partitions = request_line.split()
        if len(partitions) != 3:
            raise ValueError(request_line)
        method, path, version = partitions
        return method, path, version

    def get_response_status(path: str) -> str:
        response_status = ""
        match path:
            case "/":
                response_status = "200 OK"
            case _:
                response_status = "404 Not Found"
        return response_status

    while True:
        client_connection, _ = listen_socket.accept()

        request = client_connection.recv(BUFFER_SIZE)

        _, path, _ = parse_request_line(request)
        response_status = get_response_status(path)

        http_response = f"{HTTP_VERSION} {response_status}{HTTP_LB}"

        client_connection.sendall(http_response.encode("utf-8"))
        client_connection.close()


if __name__ == "__main__":
    main()
