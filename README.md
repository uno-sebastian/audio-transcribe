# audio-transcribe

Local, free transcription of audio and video files (English). Built for iPhone
recordings: Voice Memos (`.m4a`) and videos (`.mov`, `.mp4`).

Everything runs on your machine; no audio is uploaded anywhere.

## How it works

1. `ffmpeg` strips any input down to 16 kHz mono WAV (video is just audio extraction).
2. [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`large-v3`) transcribes it with timestamps.
3. Output goes to `transcripts/<name>.txt`.

## Setup (Windows)

```powershell
winget install Gyan.FFmpeg
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Use

```powershell
python transcribe.py recording.m4a
python transcribe.py clip.mov --model medium --device cpu
```

## iPhone file formats

- Voice Memos: `.m4a` (AAC). Share/AirDrop/export from the Voice Memos app.
- Video: `.mov` (H.264 or HEVC) by default, `.mp4` if "Most Compatible" is set. ffmpeg handles all of these.

## Roadmap

- Parakeet TDT engine as a second opinion on English audio
- Speaker labels (pyannote diarization)
- Diff two engines' output to find spots needing cleanup
