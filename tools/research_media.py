"""Exercise the existing upstream SFD pipeline on one user-provided clip."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from cutscenes import CutsceneJob, build_cutscene, _ffprobe_duration, _demux_sfd_via_ffmpeg
from ffmpeg import find_or_build_ffmpeg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--iso", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "build" / "media-probe")
    args = p.parse_args()
    out = args.out.resolve()
    if not any(out.is_relative_to(ROOT / d) for d in ("work", "build")):
        raise ValueError("output must be under ignored work/ or build/")
    import pycdlib
    out.mkdir(parents=True, exist_ok=True)
    cd = pycdlib.PyCdlib()
    cd.open(str(args.iso.resolve()))
    try:
        cd.get_file_from_iso(local_path=str(out / "original.SFD"), iso_path="/MOVIE18/180216.SFD;1")
    finally:
        cd.close()
    shutil.copyfile(ROOT / "subs/korean/180216.ass", out / "sample.ass")
    previous = Path.cwd()
    try:
        os.chdir(out)
        ff = find_or_build_ffmpeg()
        src = out / "original.SFD"
        duration = _ffprobe_duration(src)
        job = CutsceneJob("180216", "MOVIE18/180216.SFD", src, src, Path("sample.ass"),
                          src.stat().st_size, src.stat().st_size, duration, duration, "kr")
        built = build_cutscene(job, Path("."), ff, hardsub=True)
        _demux_sfd_via_ffmpeg(built, out / "rebuilt.m1v", out / "rebuilt.sfa", ff)
        a, b = (out / "180216/180216.sfa").read_bytes(), (out / "rebuilt.sfa").read_bytes()
        result = {"input_duration": duration, "output_duration": _ffprobe_duration(built),
                  "audio_equal": a == b, "input_audio_sha256": hashlib.sha256(a).hexdigest(),
                  "output_audio_sha256": hashlib.sha256(b).hexdigest(),
                  "output_size": built.stat().st_size, "output": str(built.resolve()),
                  "ffmpeg": str(ff)}
        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
        print(json.dumps(result, indent=2))
        if not result["audio_equal"]:
            raise ValueError("audio elementary stream changed")
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    main()
