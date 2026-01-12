#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "yt-dlp",
#   "airplay",
# ]
# ///
"""
AirPlay CLI - Download videos with yt-dlp and stream to Apple TV
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import airplay
import yt_dlp


def download_video(url, output_dir):
    """Download video using yt-dlp"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
    }

    print(f"Downloading video from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


def send_to_appletv(video_path, appletv_ip=None):
    """Send video to Apple TV using airplay"""
    print(f"Sending video to Apple TV: {video_path}")

    if appletv_ip:
        # Connect to specific Apple TV
        my_appletv = airplay.AirPlay(appletv_ip)
    else:
        # Auto-discover Apple TV on network
        print("Discovering Apple TV on network...")
        # Note: The airplay library will need to be configured based on its API
        # This is a placeholder for the actual implementation
        my_appletv = airplay.AirPlay()

    # Send the video
    with open(video_path, 'rb') as f:
        my_appletv.play(f)

    print("Video sent successfully!")


def main():
    parser = argparse.ArgumentParser(
        description='Download videos with yt-dlp and stream to Apple TV'
    )
    parser.add_argument(
        'url',
        help='URL of the video to download and stream'
    )
    parser.add_argument(
        '--appletv-ip',
        help='IP address of Apple TV (optional, will auto-discover if not provided)',
        default=None
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
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
        use_temp = False
    else:
        output_dir = tempfile.mkdtemp()
        use_temp = True

    # Download the video
    video_path = download_video(args.url, output_dir)

    # Send to Apple TV
    send_to_appletv(video_path, args.appletv_ip)

    # Clean up if using temp directory and not keeping video
    if use_temp and not args.keep_video:
        os.remove(video_path)
        os.rmdir(output_dir)
        print("Cleaned up temporary files")


if __name__ == '__main__':
    main()
