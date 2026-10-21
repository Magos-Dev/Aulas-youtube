#!/usr/bin/env python3
"""
Servidor local para Aura Café
Abra em: http://localhost:8000
"""

import http.server
import socketserver
import os

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"🍰 Aura Café rodando em: http://localhost:{PORT}")
    print(f"Pressione Ctrl+C para parar o servidor")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Servidor encerrado")
