import socket
import threading
from typing import Optional
import argparse
from pathlib import Path

HOST, PORT = "", 4221
BUFFER_SIZE = 1024
HTTP_VERSION = "HTTP/1.1"
CRLF = "\r\n"
HTTP_HEADER_END = CRLF * 2


class HTTPRequest:
    def __init__(self, request_text: str):
        self.method, self.path, self.version, self.body, self.headers = (
            self._parse_request(request_text)
        )

    @staticmethod
    def _parse_request(
        request_text: str,
    ) -> tuple[str, str, str, Optional[str], dict[str, str]]:
        headers_part, _, body = request_text.partition(HTTP_HEADER_END)
        lines = headers_part.split(CRLF)
        method, path, version = lines[0].split(" ")
        headers = {
            line.split(": ")[0]: line.split(": ")[1]
            for line in lines[1:]
            if ": " in line
        }
        return method, path, version, body if body else None, headers


class HTTPResponse:
    def __init__(self, request: HTTPRequest, base_dir: Path):
        self.request = request
        self.base_dir = base_dir
        self.status_code = "200"
        self.status_text = "OK"
        self.headers = {"Content-Type": "text/plain"}
        self.body = ""
        self._process_request()

    def _process_request(self):
        if self.request.method == "GET":
            self._handle_get_request()
        elif self.request.method == "POST":
            self._handle_post_request()

        if self.body:
            self.headers["Content-Length"] = str(len(self.body))

    def _handle_get_request(self):
        if self.request.path == "/":
            self.body = "Home page"
        elif self.request.path.startswith("/echo/"):
            self.body = self.request.path[6:]
        else:
            file_path = self.base_dir / self.request.path.strip("/")
            if file_path.is_file():
                self.body = file_path.read_text()
                self.headers["Content-Type"] = "application/octet-stream"
            else:
                self._set_response_not_found()

    def _handle_post_request(self):
        file_path = self.base_dir / self.request.path.strip("/")
        file_path.write_text(self.request.body or "")
        self._set_response_created()

    def _set_response_not_found(self):
        self.status_code = "404"
        self.status_text = "Not Found"
        self.body = "Page not found"

    def _set_response_created(self):
        self.status_code = "201"
        self.status_text = "Created"

    def build_response(self) -> bytes:
        status_line = f"{HTTP_VERSION} {self.status_code} {self.status_text}{CRLF}"
        headers = CRLF.join(f"{key}: {value}" for key, value in self.headers.items())
        return f"{status_line}{headers}{HTTP_HEADER_END}{self.body}".encode("utf-8")


def handle_client_connection(client_connection: socket.socket, base_dir: Path):
    try:
        request_data = client_connection.recv(BUFFER_SIZE).decode("utf-8")
        request = HTTPRequest(request_data)
        response = HTTPResponse(request, base_dir)
        client_connection.sendall(response.build_response())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="./files", type=Path)
    args = parser.parse_args()

    base_dir = args.directory.absolute()
    listen_socket = socket.create_server((HOST, PORT), reuse_port=True)
    listen_socket.listen(5)
    print(f"Serving HTTP on port {PORT}...")

    while True:
        client_connection, _ = listen_socket.accept()
        client_thread = threading.Thread(
            target=handle_client_connection, args=(client_connection, base_dir)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
