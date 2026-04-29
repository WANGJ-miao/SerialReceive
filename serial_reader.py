#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read from a serial port, filter out 0x00 bytes, and save the remaining data."
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        default="COM11",
        help="Serial port name, for example COM3 or /dev/ttyUSB0",
    )
    parser.add_argument(
        "-b",
        "--baudrate",
        type=int,
        default=921600,
        help="Baud rate, default: 921600",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="data/serial_output.bin",
        help="Output file path, default: serial_output.bin",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1.0,
        help="Serial read timeout in seconds, default: 1.0",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="Bytes to read per cycle, default: 4096",
    )
    return parser.parse_args()


def filter_null_bytes(data: bytes) -> bytes:
    return data.replace(b"\x00", b"")


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_read = 0
    total_saved = 0

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            timeout=args.timeout,
        ) as ser, output_path.open("ab") as output_file:
            print(f"Listening on {args.port} @ {args.baudrate} bps")
            print(f"Saving filtered data to: {output_path.resolve()}")
            print("Data is saved as raw filtered bytes for later plotting and analysis.")
            print("Press Ctrl+C to stop.")

            while True:
                waiting = ser.in_waiting
                read_size = waiting if waiting > 0 else args.chunk_size
                data = ser.read(read_size)
                if not data:
                    continue

                total_read += len(data)
                filtered = filter_null_bytes(data)
                if not filtered:
                    continue

                output_file.write(filtered)
                output_file.flush()

                total_saved += len(filtered)
                removed = len(data) - len(filtered)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"[{timestamp}] received={len(data)} saved={len(filtered)} filtered_0x00={removed} "
                    f"total_read={total_read} total_saved={total_saved}"
                )
    except KeyboardInterrupt:
        print("\nStopped by user.")
        print(f"Total read: {total_read} bytes")
        print(f"Total saved after filtering: {total_saved} bytes")
        return 0
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
