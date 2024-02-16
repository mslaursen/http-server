import socket
from typing import Any

HOST, PORT = "", 4221
listen_socket = socket.create_server((HOST, PORT), reuse_port=True)
listen_socket.listen(1)

HTTP_VERSION = "HTTP/1.1"
CRLF = "\r\n"
HTTP_LB = CRLF * 2
BUFFER_SIZE = 1024

print(f"Serving HTTP on port {PORT}")


class ResponseStringBuilder:
    def __init__(self):
        self._response = []

    def add_line(self, line: str):
        self._response.append(line)
        return self

    def add_lines(self, lines: list[str]):
        self._response.extend(lines)
        return self

    def add_break(self):
        self._response.extend("")
        return self

    def build(self) -> str:
        return CRLF.join(self._response)


class HTTPRequest:
    def __init__(self, request_bytes: bytes) -> None:
        try:
            self.request_text = request_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("Error decoding request bytes") from e

        self.method = None
        self.path = None
        self.version = None
        self.headers = {}
        self._parse_request_line()
        self._parse_headers()

    def _parse_request_line(self) -> None:
        request_line = self.request_text.split(CRLF)[0]
        partitions = request_line.split()
        if len(partitions) != 3:
            raise ValueError(request_line)
        self.method, self.path, self.version = partitions

    def _parse_headers(self) -> None:
        headers_dict = {}
        for header in self.request_text.split(CRLF)[1:]:
            partitions = header.split(" ")
            if len(partitions) == 2:
                key, value = partitions
                key.replace(":", "")
                headers_dict[key] = value
        self.headers: dict[str, str] = headers_dict

    def __repr__(self) -> str:
        return self.request_text


class HTTPResponse:

    def __init__(self, request: HTTPRequest) -> None:
        self.request = request
        self.status_code: str
        self.status_text: str
        self.body: str | None = None
        self.representation_headers: dict[str, Any] = {}
        self._process_request()

    def _process_request(self) -> None:
        code = ""
        text = ""
        body = ""
        path = self.request.path
        if path is None:
            raise ValueError("Path was not found.")
        if path == "/":
            code = "200"
            text = "OK"
        elif path.startswith("/echo/"):
            code = "200"
            text = "OK"
            body = path[6:]
            self.representation_headers["Content-Type"] = "text/plain"
            self.representation_headers["Content-Length"] = str(len(body))

        else:
            code = "404"
            text = "Not Found"
            # import sys

            # sys.exit(1)
        self.status_code = code
        self.status_text = text
        self.body = body

    @property
    def status_line(self) -> str:
        return f"{HTTP_VERSION} {self.status_code} {self.status_text}"

    @property
    def headers_list(self) -> list[str]:
        return sorted(
            [f"{key}: {value}" for key, value in self.representation_headers.items()]
        )

    def __repr__(self) -> str:
        builder = ResponseStringBuilder()
        response_text = builder.add_line(self.status_line).add_lines(self.headers_list)
        if self.body:
            response_text.add_break().add_line(self.body)
        return response_text.build()


def main() -> None:
    while True:
        client_connection, _ = listen_socket.accept()

        request = HTTPRequest(client_connection.recv(BUFFER_SIZE))
        response = HTTPResponse(request)

        client_connection.sendall(repr(response).encode("utf-8"))
        client_connection.close()


if __name__ == "__main__":
    main()
