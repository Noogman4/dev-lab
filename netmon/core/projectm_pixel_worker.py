"""Fixed X11-to-raw-RGBA reader, only inside its private Bubblewrap capsule."""

import os
import resource
import sys

if __package__:
    from .projectm_profile import from_arguments
else:
    import runpy

    from_arguments = runpy.run_path("/run/projectm-profile.py")["from_arguments"]


def main():
    try:
        profile = from_arguments(sys.argv[1:])
    except ValueError:
        return 2
    for name, maximum in (
        (resource.RLIMIT_AS, 768 * 1024**2),
        (resource.RLIMIT_FSIZE, 16 * 1024**2),
        (resource.RLIMIT_NOFILE, 128),
    ):
        soft, hard = resource.getrlimit(name)
        bound = min(
            [maximum] + [n for n in (soft, hard) if n != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (bound, bound))
    os.umask(0o077)
    os.execv(
        "/usr/bin/ffmpeg",
        [
            "/usr/bin/ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-threads",
            "1",
            "-filter_threads",
            "1",
            "-probesize",
            "32",
            "-analyzeduration",
            "1",
            "-fpsprobesize",
            "0",
            "-f",
            "x11grab",
            "-draw_mouse",
            "0",
            "-video_size",
            profile.key,
            "-framerate",
            "30",
            "-i",
            ":1.0+0,0",
            "-an",
            "-sn",
            "-dn",
            "-threads",
            "1",
            "-pix_fmt",
            "rgba",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(2)
