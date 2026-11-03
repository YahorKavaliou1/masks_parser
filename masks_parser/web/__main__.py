import argparse

from masks_parser.web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="masks-parser-web", description="Веб-интерфейс сверки артикулов.")
    parser.add_argument("--host", default="127.0.0.1", help="адрес (в Docker — 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="порт")
    args = parser.parse_args()
    shown_host = "localhost" if args.host in ("0.0.0.0", "127.0.0.1") else args.host
    print(f"Откройте в браузере: http://{shown_host}:{args.port}")
    create_app().run(host=args.host, port=args.port)


main()
