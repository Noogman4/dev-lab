NetMon projectM PCM adapter - local development profile, 2026-11-09

No runtime compilation and no prebuilt executable checked into source control.
Explicit local build from repository root:
  python3 -B -X pycache_prefix=/nonexistent scripts/build_projectm_pcm.py
The build/ directory is ignored. Both executable and build.json are required.
GPU counterpart: run the same command with --gpu to explicitly build
egl-renderer and egl-build.json. Both variants share PCM/preset handling;
the GPU manifest additionally hashes egl_context.hpp. Never build at startup.
The loader checks native source/header digests, executable digest/mode and the
exact installed projectM library digest. A missing/stale build fails closed.
This is a consistency check, not protection against arbitrary same-UID host code,
a reproducible build attestation or package/install approval. No packaging
integration or broad platform/version support is claimed by this prototype.

Supported payload only: installed projectM 3.1.13 x86_64 Flatpak files from
upstream commit 521eff97a5b9603ef9db58fcef4e8f1c87fae2b6.
libprojectM.so.3 SHA256:
ca7e592e283ce782e772fa0d870dbd0d5910cbdeaa8c019ce6075a1247661730
The adapter uses direct internal GLX video, no SDL/Pulse audio capture.
The library's inline C++ PCM accessor requires the matching headers; no ABI
or compatibility claim for other projectM 3/4 builds is made.

include/ contains unchanged upstream headers from that exact commit:
  src/libprojectM/{projectM.hpp,PCM.hpp,dlldefs.h,event.h,fatal.h,Common.hpp}
Source base:
https://github.com/projectM-visualizer/projectm/tree/521eff97a5b9603ef9db58fcef4e8f1c87fae2b6/src/libprojectM
Copyright/license notices remain in each header. LGPL-2.1 license is included.

Input: only float32 little-endian, 44100 Hz, interleaved stereo on stdin.
Fixed 4096-byte buffer = 512 stereo frames = 1024 float values per full API call.
Finite values clamped to [-1,1]; NaN/Inf and incomplete stereo EOF rejected.
Maximum four blocks per 40-ms tick, fixed 640x480 internal window and target
25 FPS. First/full-block deadline 5 s; partial bytes do not extend it.
Valid final short aligned block is consumed once. EOF ends the renderer.
Only NMPM1 READY\n is written to the status pipe after first PCM/render.
No audio-server socket, desktop X authority, GPU device or NetMon IPC grant.
The preceding fixed geometry/tick/no-GPU statements describe the original CPU
profile. Current CPU profiles support four resolutions and 25/30 FPS. The GPU
variant uses one explicitly selected DRM render node and EGL Desktop OpenGL,
fixed 30 FPS, mesh 220x125, a bounded profile marker and top-down RGBA frames.
It verifies both a non-software GL renderer and an open FD to that node.
No host X/Wayland/audio socket is granted. CPU/RAM quotas do not bound GPU time
or VRAM. That residual risk was explicitly accepted by the user on 2026-11-10.
Locally exercised: AMD amdgpu/Mesa. Other Mesa driver profiles are candidates;
proprietary NVIDIA and ambiguous multi-GPU selection are not implemented.
Per-process limits are not aggregate CPU/PID/RAM/tmpfs quotas.
EOF/readiness/pixel counts are not independent proof of real-world audio.
