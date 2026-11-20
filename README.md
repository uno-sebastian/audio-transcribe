# audio-transcribe

Local, free transcription of audio and video files (English). Built for iPhone
recordings: Voice Memos (`.m4a`) and videos (`.mov`, `.mp4`).

Everything runs on your machine; no audio is uploaded anywhere.

## How it works

1. `ffmpeg` strips any input down to 16 kHz mono WAV (video is just audio extraction).
2. One of two engines transcribes it with timestamps:
   - `whisper` (default): [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `large-v3`, runs on an NVIDIA GPU.
   - `parakeet`: NVIDIA Parakeet TDT 0.6B v2 (English) through [onnx-asr](https://github.com/istupakov/onnx-asr), runs on CPU.
3. Output goes to `transcripts/<name>.<engine>.txt`, so both engines' results can sit side by side.

## Setup (Windows)

```powershell
winget install Gyan.FFmpeg
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Use

```powershell
python transcribe.py recording.m4a --device cuda
python transcribe.py recording.m4a --engine parakeet
python transcribe.py clip.mov --model medium --device cpu
```

## Compare two engines

Run both engines, then list every spot where they disagree, with timestamps:

```powershell
python compare.py transcripts	alk.whisper.txt transcripts	alk.parakeet.txt --ignore-fillers
```

Where the engines agree the text is probably right; the differing spots are where to listen and fix by hand.

## iPhone file formats

- Voice Memos: `.m4a` (AAC). Share/AirDrop/export from the Voice Memos app.
- Video: `.mov` (H.264 or HEVC) by default, `.mp4` if "Most Compatible" is set. ffmpeg handles all of these.

## Roadmap

- Speaker labels (pyannote diarization)
