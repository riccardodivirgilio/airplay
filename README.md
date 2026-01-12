# AirPlay CLI

Download videos with yt-dlp and stream them to Apple TV.

## Installation

```bash
pip install -r requirements.txt
```

## First Time Setup - Pairing with Apple TV

Before you can stream videos, you need to pair with your Apple TV once. Run:

```bash
uv run --with pyatv atvremote wizard
```

This will:
1. Scan for Apple TV devices on your network
2. Guide you through pairing (you'll enter a PIN shown on your TV)
3. Save credentials to `~/.pyatv.conf`

After pairing once, you can use the CLI without needing to pair again.

## Usage

Basic usage (auto-discovers Apple TV on network):
```bash
uv run airplay/__main__.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Or if you have the script executable:
```bash
./airplay/__main__.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Keep the downloaded video:
```bash
uv run airplay/__main__.py "https://www.youtube.com/watch?v=VIDEO_ID" --keep-video
```

Save to specific directory:
```bash
uv run airplay/__main__.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir ./videos
```

## Options

- `url` - URL of the video to download and stream (required)
- `--keep-video` - Keep the downloaded video file after streaming
- `--output-dir` - Directory to save the video (default: temporary directory)

## Dependencies

- yt-dlp - For downloading videos
- pyatv - For streaming to Apple TV via AirPlay

## Troubleshooting

If you get authentication errors, you may need to re-pair:
```bash
uv run --with pyatv atvremote wizard
```
