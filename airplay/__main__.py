#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "yt-dlp",
#   "pyatv",
# ]
# ///
"""
AirPlay CLI - Download videos with yt-dlp and stream to Apple TV
"""
import argparse
import asyncio
import os
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path

import pyatv
import yt_dlp


def download_video(url, output_dir):
    """Download video using yt-dlp"""
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'extractor_args': {'youtube': {'remote_components': 'github'}},
        'merge_output_format': 'mp4',
    }

    print(f"Downloading video from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


def start_http_server(directory):
    """Start HTTP server in a thread to serve video files"""
    import socket

    # Find an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]

    os.chdir(directory)
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


async def discover_appletv():
    """Discover and connect to Apple TV"""
    print("Discovering Apple TV on network...")

    loop = asyncio.get_event_loop()
    atvs = await pyatv.scan(loop, timeout=5)

    if not atvs:
        print("No Apple TV devices found on the network")
        sys.exit(1)

    print(f"Found {len(atvs)} Apple TV device(s)")
    atv_config = atvs[0]
    print(f"Connecting to: {atv_config.name}")

    atv = await pyatv.connect(atv_config, loop)
    return atv


async def play_video(atv, video_path):
    """Play video on Apple TV"""
    # Start HTTP server to serve the video file
    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    httpd, port = start_http_server(video_dir)

    # Get local IP address
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()

    video_url = f"http://{local_ip}:{port}/{video_filename}"
    print(f"Streaming video from: {video_url}")

    await atv.stream.play_url(video_url)

    print("Video sent successfully!")

    # Keep server running for a bit to allow streaming
    await asyncio.sleep(5)

    httpd.shutdown()
    atv.close()


async def main_async(url, output_dir, keep_video):
    """Async main function"""
    use_temp = output_dir is None
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    # Discover Apple TV first
    atv = await discover_appletv()

    # Download the video after we know Apple TV is available
    video_path = download_video(url, output_dir)

    # Play video
    try:
        await play_video(atv, video_path)
    except Exception as e:
        if "not authenticated" in str(e) or "AuthenticationError" in str(type(e).__name__):
            print("\nAuthentication Error: You need to pair with your Apple TV first.")
            print("Run this command to pair:")
            print("  uv run --with pyatv atvremote wizard")
            print("\nOr manually pair with:")
            print("  uv run --with pyatv atvremote --id <device_id> --protocol airplay pair")
            sys.exit(1)
        raise

    # Clean up if using temp directory and not keeping video
    if use_temp and not keep_video:
        os.remove(video_path)
        os.rmdir(output_dir)
        print("Cleaned up temporary files")


def main():
    parser = argparse.ArgumentParser(
        description='Download videos with yt-dlp and stream to Apple TV'
    )
    parser.add_argument(
        'url',
        help='URL of the video to download and stream'
    )
    parser.add_argument(
        '--keep-video',
        action='store_true',
        help='Keep the downloaded video file (default: delete after streaming)'
    )
    parser.add_argument(
        '--output-dir',
        help='Directory to save the video (default: temporary directory)',
        default=None
    )

    args = parser.parse_args()

    # Set up output directory
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

    asyncio.run(main_async(args.url, args.output_dir, args.keep_video))


if __name__ == '__main__':
    main()
