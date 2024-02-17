import socket
import threading
from typing import Any
import argparse
from pathlib import Path


HOST, PORT = "", 4221
BUFFER_SIZE = 1024
HTTP_VERSION = "HTTP/1.1"
CRLF = "\r\n"
HTTP_LB = CRLF * 2


class HTTPRequest:
    def __init__(self, request_text: str):
        self.method, self.path, self.version, self.headers = self._parse_request(
            request_text
        )

    @staticmethod
    def _parse_request(request_text: str) -> tuple[str, str, str, dict[str, Any]]:
        lines = request_text.split(CRLF)
        method, path, version = lines[0].split(" ")
        headers = {
            line.split(": ")[0]: line.split(": ")[1]
            for line in lines[1:]
            if ": " in line
        }
        return method, path, version, headers


class HTTPResponse:
    def __init__(
        self,
        request: HTTPRequest,
        parsed_args: argparse.Namespace | None,
    ):
        self.request = request
        self.parsed_args = parsed_args
        self.status_code = "200"
        self.status_text = "OK"
        self.headers = {"Content-Type": "text/plain"}
        self.body = None
        self._process_request()

    def _process_request(self) -> None:
        path_header = self.request.path[1:].title()
        if self.request.path == "/":
            self.body = "Home page"
        elif self.request.path.startswith("/echo/"):
            self.body = self.request.path[6:]
        elif self.request.headers.get(path_header, None):
            self.body = self.request.headers[path_header]
        elif self.request.path.startswith("/files/"):
            if self.parsed_args is None:
                raise ValueError("Directory not given.")

            files_dir: Path = Path(__file__).parent.parent / self.parsed_args.directory
            if not files_dir.is_dir():
                raise ValueError("Directory does not exist")

            file_path = files_dir / self.request.path[7:]
            if not file_path.exists():
                self._set_response_not_found()
                return

            with open(file_path, "r") as f:
                self.body = f.read()
            self.headers["Content-Type"] = "application/octet-stream"
        else:
            self._set_response_not_found()

        if self.body is not None:
            self.headers["Content-Length"] = str(len(self.body))

    def _set_response_not_found(self) -> None:
        self.status_code = "404"
        self.status_text = "Not Found"
        self.body = "Page not found"

    def build_response(self) -> bytes:
        status_line = f"{HTTP_VERSION} {self.status_code} {self.status_text}{CRLF}"
        headers = CRLF.join([f"{key}: {value}" for key, value in self.headers.items()])
        return f'{status_line}{headers}{HTTP_LB}{self.body or ""}'.encode("utf-8")


def handle_client_connection(
    client_connection: socket.socket, parsed_args: argparse.Namespace
) -> None:
    try:
        request_data = client_connection.recv(BUFFER_SIZE).decode("utf-8")
        request = HTTPRequest(request_data)
        response = HTTPResponse(request, parsed_args)
        client_connection.sendall(response.build_response())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="./files", type=str)

    listen_socket = socket.create_server((HOST, PORT))
    listen_socket.listen(5)
    print(f"Serving HTTP on port {PORT}...")

    while True:
        client_connection, _ = listen_socket.accept()
        client_thread = threading.Thread(
            target=handle_client_connection,
            args=(client_connection, parser.parse_args()),
        )
        client_thread.start()


if __name__ == "__main__":
    main()
