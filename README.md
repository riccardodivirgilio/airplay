# AirPlay CLI

Download videos with yt-dlp and stream them to Apple TV.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python -m airplay "https://www.youtube.com/watch?v=VIDEO_ID"
```

Specify Apple TV IP address:
```bash
python -m airplay "https://www.youtube.com/watch?v=VIDEO_ID" --appletv-ip 192.168.1.100
```

Keep the downloaded video:
```bash
python -m airplay "https://www.youtube.com/watch?v=VIDEO_ID" --keep-video
```

Save to specific directory:
```bash
python -m airplay "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir ./videos
```

## Options

- `url` - URL of the video to download and stream (required)
- `--appletv-ip` - IP address of Apple TV (optional, will auto-discover if not provided)
- `--keep-video` - Keep the downloaded video file after streaming
- `--output-dir` - Directory to save the video (default: temporary directory)

## Dependencies

- yt-dlp - For downloading videos
- airplay - For streaming to Apple TV
