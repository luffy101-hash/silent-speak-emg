"""UDP receiver for Wi-Fi EMG stream (optional wearable mode)."""

from __future__ import annotations

import argparse
import socket

from preprocess import parse_csv_line


def listen_udp(host: str = "0.0.0.0", port: int = 5005) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"UDP listening on {host}:{port}")

    while True:
        data, addr = sock.recvfrom(1024)
        line = data.decode("utf-8", errors="ignore")
        parsed = parse_csv_line(line)
        if parsed:
            ts, values = parsed
            print(f"{addr[0]}  t={ts}  ch={values.tolist()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5005)
    args = parser.parse_args()
    listen_udp(port=args.port)


if __name__ == "__main__":
    main()
