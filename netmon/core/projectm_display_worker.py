"""Fixed internal Xvfb entrypoint, invoked only inside Bubblewrap."""

import os
import resource
import sys

if __package__:
    from .projectm_profile import from_arguments
else:
    import runpy

    from_arguments = runpy.run_path("/run/projectm-profile.py")["from_arguments"]


def limits():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    bound = min(
        [2 * 1024 * 1024 * 1024]
        + [x for x in (soft, hard) if x != resource.RLIM_INFINITY]
    )
    resource.setrlimit(resource.RLIMIT_AS, (bound, bound))


def main():
    try:
        profile = from_arguments(sys.argv[1:])
    except ValueError:
        return 2
    limits()
    os.umask(0o077)
    os.execv(
        "/usr/bin/Xvfb",
        [
            "/usr/bin/Xvfb",
            ":1",
            "-screen",
            "0",
            f"{profile.width}x{profile.height}x24",
            "-nolisten",
            "tcp",
            "-noreset",
            "-iglx",
            "-auth",
            "/run/private.auth",
        ],
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(2)
