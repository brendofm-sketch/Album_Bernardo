#!/usr/bin/env python3
"""Servidor local para abrir o album no tablet pela rede."""

from __future__ import annotations

import http.server
import socket
import socketserver
from pathlib import Path


PORT = 8765
ROOT = Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as server:
        ip = local_ip()
        print("Album da Copa 2026")
        print(f"Computador: http://localhost:{PORT}/album_copa_2026_premium_imagens_externas.html")
        print(f"Tablet na mesma rede: http://{ip}:{PORT}/album_copa_2026_premium_imagens_externas.html")
        print("Pressione Ctrl+C para parar.")
        server.serve_forever()
