#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "yt-dlp",
#   "pyatv",
#   "rangehttpserver",
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
from http.server import HTTPServer
from pathlib import Path

import pyatv
import yt_dlp
from RangeHTTPServer import RangeRequestHandler


def download_video(url, output_dir):
    """Download video using yt-dlp"""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',
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
        s.bind(('0.0.0.0', 0))
        s.listen(1)
        port = s.getsockname()[1]

    os.chdir(directory)

    class LoggingRangeRequestHandler(RangeRequestHandler):
        def log_message(self, format, *args):
            pass

    httpd = HTTPServer(("0.0.0.0", port), LoggingRangeRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


async def connect_to_appletv():
    """Connect to Apple TV using saved configuration"""
    from pyatv.storage.file_storage import FileStorage

    loop = asyncio.get_event_loop()

    # Load the same storage that atvremote uses
    storage = FileStorage.default_storage(loop)
    await storage.load()

    if not storage.settings:
        print("No saved Apple TV configuration found.")
        print("Please pair with your Apple TV first:")
        print("  uv run --with pyatv atvremote wizard")
        sys.exit(1)

    # Scan with storage to find paired devices
    atvs = await pyatv.scan(loop, timeout=5, storage=storage)

    if not atvs:
        print("No paired Apple TV found on network.")
        print("Make sure your Apple TV is on and connected to the network.")
        sys.exit(1)

    # Find first device with AirPlay credentials
    selected_atv = None
    for atv_config in atvs:
        airplay_service = atv_config.get_service(pyatv.const.Protocol.AirPlay)
        if airplay_service and airplay_service.credentials:
            selected_atv = atv_config
            break

    if not selected_atv:
        print("No Apple TV with AirPlay credentials found.")
        print("Please pair with your Apple TV first:")
        print("  uv run --with pyatv atvremote wizard")
        sys.exit(1)

    # Connect to the selected device
    print(f"Connecting to {selected_atv.name}...")
    atv = await pyatv.connect(selected_atv, loop, storage=storage)
    return atv


async def play_video(atv, video_path, test_server=False):
    """Play video on Apple TV"""
    # Start HTTP server to serve the video file
    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    httpd, port = start_http_server(video_dir)

    # Get local IP on same network as Apple TV
    import socket
    conf = atv._config
    atv_ip = str(conf.address)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((atv_ip, 80))
    local_ip = s.getsockname()[0]
    s.close()

    from urllib.parse import quote
    video_url = f"http://{local_ip}:{port}/{quote(video_filename)}"
    print(f"Streaming {video_filename} to {atv._config.name} at {video_url}")

    # Test server if requested
    if test_server:
        import aiohttp
        print("Testing HTTP server accessibility...")
        async with aiohttp.ClientSession() as session:
            async with session.head(video_url) as resp:
                print(f"  HEAD request: status={resp.status}")
                print(f"  Content-Type: {resp.headers.get('Content-Type')}")
                print(f"  Content-Length: {resp.headers.get('Content-Length')}")
                if resp.status != 200:
                    print(f"ERROR: Server returned status {resp.status}")
                    httpd.shutdown()
                    atv.close()
                    raise Exception(f"HTTP server test failed with status {resp.status}")

    # Start playback
    await atv.stream.play_url(video_url)
    print("Playback completed!")

    httpd.shutdown()
    atv.close()


async def main_async(url_or_path, output_dir, keep_video, test_server):
    """Async main function"""
    # Connect to Apple TV using saved config
    atv = await connect_to_appletv()

    # Determine if we need to download or use existing file
    if url_or_path.startswith('http://') or url_or_path.startswith('https://'):
        # Download from URL
        use_temp = output_dir is None
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)

        video_path = download_video(url_or_path, output_dir)
    else:
        # Use local file
        video_path = url_or_path
        use_temp = False
        if not os.path.exists(video_path):
            print(f"Error: File not found: {video_path}")
            sys.exit(1)
        print(f"Using local file: {video_path}")

    # Play video
    await play_video(atv, video_path, test_server)

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
        'url_or_path',
        help='URL to download or path to local video file'
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
    parser.add_argument(
        '--test-server',
        action='store_true',
        help='Test HTTP server accessibility before streaming'
    )

    args = parser.parse_args()

    asyncio.run(main_async(args.url_or_path, args.output_dir, args.keep_video, args.test_server))


if __name__ == '__main__':
    main()
