from .auth import authenticate_google
from .json_sync import sync_json_file
from .ics_sync import sync_ics_file

from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Sync memory to Google Calendar")
    parser.add_argument("--file", type=str, required=True, help="Path to .json or .ics file")

    args = parser.parse_args()
    file_path = Path(args.file)
    service = authenticate_google()

    if file_path.suffix == ".json":
        sync_json_file(service, file_path)
    elif file_path.suffix == ".ics":
        sync_ics_file(service, file_path)
    else:
        raise ValueError("Unsupported file format. Use .json or .ics")

if __name__ == "__main__":
    main()
