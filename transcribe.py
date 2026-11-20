#!/usr/bin/env python3
"""Transcribe audio or video files (iPhone .m4a/.mov/.mp4 etc.) to text.

ffmpeg converts any input to 16 kHz mono WAV first, so video and audio
go through the same path. Engine: faster-whisper (English).

Usage:
    python transcribe.py path/to/file.m4a
    python transcribe.py path/to/video.mov --model large-v3 --out transcripts
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def add_cuda_dlls() -> None:
    """Make pip-installed CUDA libs (nvidia-cublas-cu12, nvidia-cudnn-cu12) findable on Windows."""
    import os
    import site

    for base in site.getsitepackages():
        for lib in ("cublas", "cudnn"):
            d = Path(base) / "nvidia" / lib / "bin"
            if d.is_dir():
                os.add_dll_directory(str(d))
                os.environ["PATH"] = str(d) + os.pathsep + os.environ["PATH"]


def extract_audio(src: Path, dst: Path) -> None:
    """Convert any audio/video file to 16 kHz mono WAV with ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vn",              # drop video stream
        "-ac", "1",         # mono
        "-ar", "16000",     # 16 kHz
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        sys.exit("ffmpeg not found. Install it (e.g. `winget install Gyan.FFmpeg`) and reopen your terminal.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg failed:\n{e.stderr.decode(errors='replace')}")


def fmt_ts(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def whisper_segments(wav: Path, args):
    """faster-whisper engine. Yields (start_seconds, text)."""
    add_cuda_dlls()
    from faster_whisper import WhisperModel  # imported late so --help is fast

    print(f"Loading faster-whisper {args.model} ...")
    model = WhisperModel(args.model, device=args.device, compute_type="auto")
    segments, _info = model.transcribe(
        str(wav),
        language="en",
        vad_filter=True,                  # skip silence; reduces hallucinations
        # Keeping context lets the model carry capitalization/punctuation
        # style forward; turning it off made output all-lowercase.
        condition_on_previous_text=True,
        initial_prompt="Hello. This is a conversation, transcribed with proper punctuation and capitalization.",
        temperature=[0.0, 0.2, 0.4],      # fall back if decoding gets stuck in a loop
    )
    for seg in segments:
        yield seg.start, seg.text.strip()


def parakeet_segments(wav: Path, args):
    """NVIDIA Parakeet TDT 0.6B v2 (English) via onnx-asr. Yields (start_seconds, text)."""
    import onnx_asr

    print("Loading Parakeet TDT 0.6B v2 ...")
    providers = ["CPUExecutionProvider"]  # fast enough on CPU; GPU is optional
    model = onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v2", providers=providers)
    vad = onnx_asr.load_vad("silero", providers=providers)  # splits long audio into chunks
    for seg in model.with_vad(vad).recognize(str(wav)):
        yield seg.start, seg.text.strip()


ENGINES = {"whisper": whisper_segments, "parakeet": parakeet_segments}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path, help="audio or video file")
    p.add_argument("--engine", choices=ENGINES, default="whisper", help="whisper (default) or parakeet")
    p.add_argument("--model", default="large-v3", help="faster-whisper model (whisper engine only)")
    p.add_argument("--device", default="auto", help="auto, cpu, or cuda (whisper engine only)")
    p.add_argument("--out", type=Path, default=Path("transcripts"), help="output folder")
    args = p.parse_args()

    if not args.input.exists():
        sys.exit(f"File not found: {args.input}")

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        print(f"Extracting audio from {args.input.name} ...")
        extract_audio(args.input, wav)

        print("Transcribing ...")
        txt_path = args.out / f"{args.input.stem}.{args.engine}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for start, text in ENGINES[args.engine](wav, args):
                line = f"[{fmt_ts(start)}] {text}"
                print(line)
                f.write(line + "\n")

    print(f"\nSaved: {txt_path}")


if __name__ == "__main__":
    main()
