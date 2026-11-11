"""Fixed projectM PCM entrypoint; only invoked inside the renderer sandbox."""

import os
import resource
import sys

if __package__:
    from .projectm_profile import renderer_arguments
else:
    import runpy

    renderer_arguments = runpy.run_path("/run/projectm-profile.py")[
        "renderer_arguments"
    ]


def limits():
    for name, maximum in (
        (resource.RLIMIT_AS, 2 * 1024**3),
        (resource.RLIMIT_FSIZE, 16 * 1024**2),
        (resource.RLIMIT_NOFILE, 256),
    ):
        bounds = resource.getrlimit(name)
        maximum = min([maximum] + [x for x in bounds if x != resource.RLIM_INFINITY])
        resource.setrlimit(name, (maximum, maximum))


def main():
    try:
        profile, cpu = renderer_arguments(sys.argv[1:])
    except ValueError:
        return 2
    limits()
    os.umask(0o077)
    os.execv(
        "/app/bin/pcm-renderer",
        ["/app/bin/pcm-renderer", profile.key, cpu.key],
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(2)
