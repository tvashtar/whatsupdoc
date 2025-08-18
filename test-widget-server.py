#!/usr/bin/env python3
"""Simple HTTP server to test the widget locally"""

import http.server
import socketserver
import os

PORT = 8888
DIRECTORY = "."

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

os.chdir('/Users/conor/repos/whatsupdoc')
with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print(f"Open http://localhost:{PORT}/test-widget-local.html to test the widget")
    print("Check browser console for debug logs from loadConfig()")
    httpd.serve_forever()
