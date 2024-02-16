import socket

HOST, PORT = "", 4221
BUFFER_SIZE = 1024
HTTP_VERSION = "HTTP/1.1"
CRLF = "\r\n"
HTTP_LB = CRLF * 2


class HTTPRequest:
    def __init__(self, request_text):
        self.method, self.path, self.version, self.headers = self.parse_request(
            request_text
        )

    @staticmethod
    def parse_request(request_text):
        lines = request_text.split(CRLF)
        method, path, version = lines[0].split(" ")
        headers = {
            line.split(": ")[0]: line.split(": ")[1]
            for line in lines[1:]
            if ": " in line
        }
        return method, path, version, headers


class HTTPResponse:
    def __init__(self, request):
        self.request = request
        self.status_code = "200"
        self.status_text = "OK"
        self.headers = {"Content-Type": "text/plain"}
        self.body = None
        self.process_request()

    def process_request(self):
        if self.request.path == "/":
            self.body = "Home page"
        elif self.request.path.startswith("/echo/"):
            self.body = self.request.path[6:]
        else:
            self.status_code = "404"
            self.status_text = "Not Found"
            self.body = "Page not found"

        if self.body is not None:
            self.headers["Content-Length"] = str(len(self.body))

    def build_response(self):
        status_line = f"{HTTP_VERSION} {self.status_code} {self.status_text}{CRLF}"
        headers = CRLF.join([f"{key}: {value}" for key, value in self.headers.items()])
        return f'{status_line}{headers}{HTTP_LB}{self.body or ""}'.encode("utf-8")


def main():
    listen_socket = socket.create_server((HOST, PORT))
    listen_socket.listen(1)
    print(f"Serving HTTP on port {PORT}...")

    while True:
        client_connection, _ = listen_socket.accept()
        try:
            request_data = client_connection.recv(BUFFER_SIZE).decode("utf-8")
            request = HTTPRequest(request_data)
            response = HTTPResponse(request)
            client_connection.sendall(response.build_response())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_connection.close()


if __name__ == "__main__":
    main()
