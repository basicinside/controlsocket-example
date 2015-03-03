#!/usr/bin/env python

"""
Tornado control socket example.

`telnet localhost 9999' connects to the controlsocket.
`http://localhost:8888` shows the welcome message `Hello World`

Use can manipulate the web output interactively from the control
socket. Send `hello <name>` to the control socket to alter the
web pages welcome message. Send `quit` to disconnect.
This can be used to i.e. modify log levels in a running process
without rebooting or changing other internal configuring states
on demand.
"""
import tornado.web
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer
import socket

__author__ = "Robin Kuck (@basicinside)"
__copyright__ = "Copyright 2015"
__credits__ = ["Robin Kuck"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Robin Kuck"
__email__ = "robin@basicinside.de"
__status__ = "Draft"

name = "World"


class MainHandler(tornado.web.RequestHandler):
    """
    Welcome message web handler
    """
    def get(self):
        self.write("Hello {}!".format(name))


class ControlSocket(TCPServer):
    """
    Control socket based on tornados TCPServer
    """
    def handle_stream(self, stream, address):
        self._stream = stream
        self._address = address
        self._read_line()

    def _read_line(self):
        self._stream.read_until('\n', self._handle_read)

    def _handle_read(self, command):
        global name
        arguments = command.strip().split(' ', 1)
        command = arguments[0]
        try:
            params = arguments[1]
        except:
            params = None
        if command == 'hello':
            name = params
        elif command == 'quit':
            self._stream.socket.shutdown(socket.SHUT_RDWR)
            self._stream.close()
            return
        else:
            response = "command '{}' not found\n".format(command)
            self._stream.write(response)
        self._read_line()


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.listen(8888)
    controlsocket = ControlSocket()
    controlsocket.listen(9999)
    IOLoop.instance().start()
