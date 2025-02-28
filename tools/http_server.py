import http.server as SimpleHTTPServer
import os
import socketserver as SocketServer

if os.getcwd() != os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))


class GetHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        print(self.headers)
        if not self.path.endswith(".json"):
            self.path = self.path + ".json"
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


# in case port is not released
SocketServer.TCPServer.allow_reuse_address = True
httpd = SocketServer.TCPServer(("", 8080), GetHandler)
httpd.allow_reuse_address = True
httpd.serve_forever()
