"""Fixed experimental internal Xvfb entrypoint, only inside the probe capsule."""

import os
import resource
import sys


def main():
    if sys.argv[1:]:
        return 2
    for name, maximum in (
        (resource.RLIMIT_AS, 2 * 1024**3),
        (resource.RLIMIT_CPU, 30),
        (resource.RLIMIT_FSIZE, 16 * 1024**2),
        (resource.RLIMIT_NOFILE, 256),
    ):
        bounds = resource.getrlimit(name)
        bound = min([maximum] + [x for x in bounds if x != resource.RLIM_INFINITY])
        resource.setrlimit(name, (bound, bound))
    os.umask(0o077)
    os.execv(
        "/usr/bin/Xvfb",
        [
            "/usr/bin/Xvfb",
            ":1",
            "-screen",
            "0",
            "640x480x24",
            "-nolisten",
            "tcp",
            "-noreset",
            "-iglx",
            "-auth",
            "/run/private.auth",
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
