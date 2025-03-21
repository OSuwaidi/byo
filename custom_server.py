import socket
from threading import Thread
import os
import argparse
import gzip

ERROR: str = "404 Not Found\r\n\r\n"
HOST = "localhost"
PORT = 4221


def main() -> None:
    parser = argparse.ArgumentParser(description="A TCP server that handles basic requests.")
    parser.add_argument(
        "--directory",
        type=str,
        help="The directory to check",
        default=".",
        required=False,
    )
    # Parse the command-line arguments:
    cli_args = parser.parse_args()

    # Create a TCP/IP server socket (endpoint), bind it to a specified host and port, then put it into listening mode
    # Note: Windows doesn't support process port-sharing (can't set reuse_port=True)
    with socket.create_server((HOST, PORT),) as server:  # create the server socket "within" a context manager
        print(f"Server listening on {HOST}:{PORT}\n")

        while True:  # keep listening...
            # Accept and establish a connection:
            connection, address = server.accept()  # blocking call (similar to input()); continuously waits (hangs) until a client connects
            # Each client's connection reruns this entire script, hence, it also instantiates a new, separate thread per connection!
            Thread(target=handle_connection, args=(connection, address, cli_args)).start()


def handle_connection(connection: socket, address: tuple, args: argparse.Namespace) -> None:
    with connection:
        print(f"Connected by {address}\n")  # client's IP address and port

        # Receive an HTTP http_request:
        http_request: str = connection.recv(1024).decode("utf-8")  # blocking call; waits for up to 1024 bytes of data to arrive (be transmitted) over the network (I/O-bound operation)
        print(f"Incoming HTTP http_request:\n{http_request}")

        request_components = http_request.removesuffix("\r\n").split("\r\n")
        request_line, *request_headers, request_body = request_components
        print(f"Request Body:\n{request_body}")

        http_method, requested_url, http_version = request_line.split(" ")

        http_response: bytes
        if http_method == "GET":
            header_dict: dict[str, str] = {header: specification for header, specification in map(lambda headers: headers.split(": "), request_headers)}

            if requested_url == "/":
                print("Client requested index page")
                # Our response must be a "byte string" (binary format) rather than a regular python string such that it's correctly interpreted by other systems
                http_response = response_template()

            elif requested_url.startswith("/echo"):
                string = requested_url.removeprefix("/echo/")
                accept_encodings = header_dict.get("Accept-Encoding")
                if accept_encodings:
                    accept_encodings = "gzip" in accept_encodings.split(", ")
                http_response = response_template(body=string, encoding=accept_encodings)

            elif requested_url.startswith("/user-agent"):
                user_agent = header_dict.get("User-Agent")
                http_response = response_template(body=user_agent)

            elif requested_url.startswith("/files"):
                file_name = requested_url.removeprefix("/files/")
                path = os.path.join(args.directory, file_name)

                if os.path.isfile(path):
                    print(f"File found at: {path}")

                    with open(path, "r") as file:
                        http_response = response_template(content_type="application/octet-stream", body=file.read())

                else:
                    print("File not found!")
                    http_response = response_template(status=ERROR)

            else:
                print("Client requested some other page")
                http_response = response_template(status=ERROR)

        else:  # if POST...
            if requested_url.startswith("/files"):
                file_name = requested_url.removeprefix("/files/")
                with open(os.path.join(args.directory, file_name), "w") as file:
                    file.write(request_body)
                    http_response = response_template(status="201 Created")

        connection.sendall(http_response)  # blocking call; waits for the network to transmit data to the client


def response_template(status: str = "200 OK",
                      encoding: bool | None = None,
                      content_type: str = "text/plain",
                      body: str = "",) -> bytes:

    encoded_body: bytes
    if encoding:
        encoded_body = gzip.compress(body.encode("utf-8"))
        encoding = f"Content-Encoding: gzip\r\n"
    else:
        encoded_body = body.encode("utf-8")
        encoding = ""

    content_headers = f"Content-Type: {content_type}\r\nContent-Length: {len(encoded_body)}\r\n" if body else ""

    return f"HTTP/1.1 {status}\r\n{encoding}{content_headers}\r\n".encode("utf-8") + encoded_body


if __name__ == "__main__":
    main()
