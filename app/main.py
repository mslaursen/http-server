import socket
import threading
from typing import Any

HOST, PORT = "", 4221
BUFFER_SIZE = 1024
HTTP_VERSION = "HTTP/1.1"
CRLF = "\r\n"
HTTP_LB = CRLF * 2


class HTTPRequest:
    def __init__(self, request_text: str):
        self.method, self.path, self.version, self.headers = self.parse_request(
            request_text
        )

    @staticmethod
    def parse_request(request_text: str) -> tuple[str, str, str, dict[str, Any]]:
        lines = request_text.split(CRLF)
        method, path, version = lines[0].split(" ")
        headers = {
            line.split(": ")[0]: line.split(": ")[1]
            for line in lines[1:]
            if ": " in line
        }
        return method, path, version, headers


class HTTPResponse:
    def __init__(self, request: HTTPRequest):
        self.request = request
        self.status_code = "200"
        self.status_text = "OK"
        self.headers = {"Content-Type": "text/plain"}
        self.body = None
        self.process_request()

    def process_request(self) -> None:
        path_header = self.request.path[1:].title()
        if self.request.path == "/":
            self.body = "Home page"
        elif self.request.path.startswith("/echo/"):
            self.body = self.request.path[6:]
        elif self.request.headers.get(path_header, None):
            self.body = self.request.headers[path_header]
        else:
            self.status_code = "404"
            self.status_text = "Not Found"
            self.body = "Page not found"

        if self.body is not None:
            self.headers["Content-Length"] = str(len(self.body))

    def build_response(self) -> bytes:
        status_line = f"{HTTP_VERSION} {self.status_code} {self.status_text}{CRLF}"
        headers = CRLF.join([f"{key}: {value}" for key, value in self.headers.items()])
        return f'{status_line}{headers}{HTTP_LB}{self.body or ""}'.encode("utf-8")


def handle_client_connection(client_connection: socket.socket) -> None:
    try:
        request_data = client_connection.recv(BUFFER_SIZE).decode("utf-8")
        request = HTTPRequest(request_data)
        response = HTTPResponse(request)
        client_connection.sendall(response.build_response())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_connection.close()


def main() -> None:
    listen_socket = socket.create_server((HOST, PORT))
    listen_socket.listen(5)
    print(f"Serving HTTP on port {PORT}...")

    while True:
        client_connection, _ = listen_socket.accept()
        client_thread = threading.Thread(
            target=handle_client_connection, args=(client_connection,)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
