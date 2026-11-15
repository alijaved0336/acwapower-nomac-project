import os
import sys
import socket


def main() -> int:
    try:
        import clickhouse_connect  # type: ignore
    except Exception as e:
        print("ERROR: clickhouse-connect is not installed. Install with: pip install clickhouse-connect", file=sys.stderr)
        print(f"Detail: {e}", file=sys.stderr)
        return 2

    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    username = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    secure = os.getenv("CLICKHOUSE_SECURE", "0") in ("1", "true", "True")

    print("Testing ClickHouse connectivity with:")
    print(f"  Host   : {host}")
    print(f"  Port   : {port}")
    print(f"  User   : {username}")
    print(f"  Secure : {secure}")

    # Quick TCP reachability check first
    try:
        with socket.create_connection((host, port), timeout=5):
            print("TCP check: SUCCESS (port reachable)")
    except Exception as e:
        print(f"TCP check: FAILED ({e})")

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            secure=secure,
        )
        pong = client.ping()
        print(f"Client ping: {pong}")

        version = client.query("select version()")
        print(f"ClickHouse version: {version.result_rows[0][0]}")

        # Optional: ensure DB exists if provided via env
        db = os.getenv("CLICKHOUSE_DB")
        if db:
            client.command(f"CREATE DATABASE IF NOT EXISTS {db}")
            client.command(f"USE {db}")
            current_db = client.query("select currentDatabase()").result_rows[0][0]
            print(f"Current database: {current_db}")

        print("Connection test: SUCCESS")
        return 0
    except Exception as e:
        print("Connection test: FAILED", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


