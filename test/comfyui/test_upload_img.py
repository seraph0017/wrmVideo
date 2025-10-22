#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests


def upload_image(url: str, image_path: str, img_type: str = "input", subfolder: str = "", timeout: int = 60) -> dict:
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    filename = os.path.basename(image_path)

    with open(image_path, "rb") as f:
        files = {"image": (filename, f, "application/octet-stream")}
        data = {"type": img_type, "subfolder": subfolder}
        resp = requests.post(url, data=data, files=files, timeout=timeout)
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}


def main():
    parser = argparse.ArgumentParser(description="Upload an image via multipart/form-data.")
    parser.add_argument("image", help="Path to the local image file")
    parser.add_argument(
        "--url",
        "-u",
        default="http://115.190.188.138:8188/api/upload/image",
        help="Target upload URL",
    )
    parser.add_argument(
        "--type",
        "-t",
        default="input",
        choices=["input", "output"],
        help="Upload type",
    )
    parser.add_argument("--subfolder", default="", help="Optional subfolder name")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")

    args = parser.parse_args()

    try:
        result = upload_image(args.url, args.image, args.type, args.subfolder, args.timeout)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    base = args.url.split("/api/upload/image")[0]
    fname = os.path.basename(args.image)
    view_url = f"{base}/view?type={args.type}&filename={fname}"
    if args.subfolder:
        view_url += f"&subfolder={args.subfolder}"
    print(f"View URL: {view_url}")


if __name__ == "__main__":
    main()