request = b"GET / HTTP/1.1\r\nHost: 127.0.0.1:4221\r\nUser-Agent: curl/7.87.0\r\nAccept: */*\r\n\r\n"
text = request.decode()

print(text)

print(text.split("\r\n")[0].split()[1])
