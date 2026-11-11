"""Fixed raw-PCM conversion inside its offline capsule."""

import os
import resource
import sys

if sys.argv[1:]:
    raise SystemExit(2)
for name, maximum in [
    (resource.RLIMIT_AS, 512 * 1024**2),
    (resource.RLIMIT_FSIZE, 16 * 1024**2),
    (resource.RLIMIT_NOFILE, 128),
]:
    limits = resource.getrlimit(name)
    maximum = min([maximum] + [x for x in limits if x != resource.RLIM_INFINITY])
    resource.setrlimit(name, (maximum, maximum))
os.umask(0o077)
os.execv(
    "/usr/bin/ffmpeg",
    [
        "/usr/bin/ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-probesize",
        "32",
        "-analyzeduration",
        "1",
        "-protocol_whitelist",
        "pipe",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-i",
        "pipe:0",
        "-threads",
        "1",
        "-filter_threads",
        "1",
        "-f",
        "f32le",
        "-ar",
        "44100",
        "-ac",
        "2",
        "pipe:1",
    ],
)
