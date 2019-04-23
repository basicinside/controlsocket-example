#!/usr/bin/env python

"""
Tornado control socket example.

`telnet localhost 9090' connects to the controlsocket.
`http://localhost:8080` shows the welcome message `Hello World!`

In this example you can alter the web output interactively from the control
socket. Send `hello <name>` to the control socket to alter the
web pages welcome message. Send `quit` to disconnect.
This can be used to i.e. modify log levels in a running process
without rebooting or changing other internal configuration state
on demand.
"""
import argparse
import logging
import re
import socket

import coloredlogs
import tornado.web
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer

PARAMS_COMMAND_PATTERN = re.compile('^(?P<command>[\\w-]+) (?P<params>.*)$')
SINGLE_COMMAND_PATTERN = re.compile('^(?P<command>[\\w-]+)$')

logger = logging.getLogger(__name__)
# XXX: argparse loglevel
coloredlogs.install(level='DEBUG')


class AppState(object):
    def __init__(self, name):
        self.name = name


class QuitSignal(Exception):
    pass


class MainHandler(tornado.web.RequestHandler):
    """
    Welcome message web handler
    """
    def initialize(self, state):
        self.state = state

    def get(self):
        self.write("Hello {}!".format(self.state.name))


class ControlSocket(TCPServer):
    """
    Control socket based on tornados TCPServer
    """
    def __init__(self, *args, state=None, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)

    async def handle_stream(self, stream, address):
        self.stream = stream
        addr = '{}:{}'.format(address[0], address[1])
        logger.debug('Incoming connection from {}'.format(addr))
        while True:
            try:
                line = await self.stream.read_until(b'\n')
                await self.handle_readline(line.decode('utf-8').strip())
            except StreamClosedError:
                break
            except QuitSignal:
                break
        logger.debug('Connection from {} closed'.format(addr))

    async def write_stream(self, message):
        await self.stream.write(bytearray(message, 'utf-8'))

    async def handle_readline(self, line):
        params_match = PARAMS_COMMAND_PATTERN.match(line)
        single_match = SINGLE_COMMAND_PATTERN.match(line)

        if params_match:
            command = params_match.group('command')
            params = params_match.group('params')

            if command == 'hello':
                self.state.name = params
            else:
                response = "command '{}' with params '{}' not found\n".format(
                        command, params)
                logger.warning(response)
                await self.write_stream(response)
        elif single_match:
            command = single_match.group('command')

            if command == 'quit':
                await self.write_stream("Goodbye!\n")
                self.stream.socket.shutdown(socket.SHUT_RDWR)
                self.stream.close()
                raise QuitSignal()
            else:
                response = "command '{}' not found\n".format(command)
                logger.warning(response)
                await self.write_stream(response)
        else:
            response = "invalid input: '{}'\n".format(line)
            logger.warning(response)
            await self.write_stream(response)


class ControlSocketApplication(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
                '--web-port', type=int, default=8080, help='web server port')
        parser.add_argument(
                '--controlsocket-port', default=9090, type=int,
                help='controlsocket port')
        self.args = parser.parse_args()

        self.state = AppState('World')

        self.application = tornado.web.Application([
            (r"/", MainHandler, dict(state=self.state)),
        ])

        self.controlsocket = ControlSocket(state=self.state)

    def execute(self):
        logger.info('Spawning controlsocket on localhost:{}'.format(
            self.args.controlsocket_port))
        self.controlsocket.listen(self.args.controlsocket_port)
        logger.info('Spawning web server on localhost:{}'.format(
            self.args.web_port))
        self.application.listen(self.args.web_port)
        IOLoop.instance().start()


def main():
    app = ControlSocketApplication()
    app.execute()


if __name__ == "__main__":
    main()
