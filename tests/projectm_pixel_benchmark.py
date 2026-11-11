"""Finite 30/60 FPS transport measurement inside the private pixel prototype.

CPU figures cover sampled descendants of this coordinator, including observer
work. Latency starts before XGetImage and ends at a complete received frame;
it is not renderer, audio synchronization or visible UI latency.
"""

import hashlib
import json
import os
from pathlib import Path
import selectors
import struct
import subprocess
import time

import psutil

from projectm_pixel_protocol import CHUNK, FRAME_BYTES

MAGIC = b"NMPB01\0"
END = 0xFFFFFFFF
DURATION = 30


def slots(fps):
    if type(fps) is not int or fps not in (30, 60):
        raise ValueError("Only trusted 30/60 FPS profiles")
    return fps * DURATION


def capture_source(fps):
    from projectm_pixel_probe import CAPTURE

    count = slots(fps)
    # Only trusted constants change, never a caller-supplied C fragment.
    changes = {
        "limit(RLIMIT_CPU,12)": "limit(RLIMIT_CPU,45)",
        'fwrite("NMPX01\\0",1,7,stdout)': 'fwrite("NMPB01\\0",1,7,stdout)',
        "for(uint32_t frame=0;frame<24;frame++){": f"""
 struct timespec start;clock_gettime(CLOCK_MONOTONIC,&start);
 uint64_t base=(uint64_t)start.tv_sec*1000000000ULL+start.tv_nsec;
 for(uint32_t frame=0;frame<{count};frame++){{
  uint64_t target=base+(uint64_t)frame*1000000000ULL/{fps};
  struct timespec due={{target/1000000000ULL,target%1000000000ULL}};
  if(clock_nanosleep(CLOCK_MONOTONIC,TIMER_ABSTIME,&due,NULL))return 11;
  struct timespec now;if(clock_gettime(CLOCK_MONOTONIC,&now))return 12;
  uint64_t stamp=(uint64_t)now.tv_sec*1000000000ULL+now.tv_nsec;
  if(stamp>=base+(uint64_t)(frame+1)*1000000000ULL/{fps})continue;
""",
        "if(fwrite(&sequence,1,4,stdout)!=4||fwrite(rgba,1,640*480*4,stdout)!=640*480*4)return 9;": """
  uint32_t high=htonl(stamp>>32),low=htonl(stamp&0xffffffff);
  if(fwrite(&sequence,1,4,stdout)!=4||fwrite(&high,1,4,stdout)!=4||
     fwrite(&low,1,4,stdout)!=4||fwrite(rgba,1,640*480*4,stdout)!=640*480*4)return 9;
""",
        "struct timespec delay={0,100000000};nanosleep(&delay,NULL);": "",
        "free(rgba);XCloseDisplay(d);return 0;": """
 uint32_t end[3]={htonl(0xffffffff),0,0};
 if(fwrite(end,1,sizeof(end),stdout)!=sizeof(end))return 13;
 free(rgba);XCloseDisplay(d);return 0;
""",
    }
    for old, new in changes.items():
        if CAPTURE.count(old) != 1:
            raise ValueError("Reader source marker changed")
        CAPTURE = CAPTURE.replace(old, new)
    return CAPTURE


class TimedDecoder:
    def __init__(self, fps):
        self.slots = slots(fps)
        self.buffer = bytearray()
        self.started = self.ended = False
        self.last = -1
        self.stamp = self.count = self.peak = 0

    def feed(self, data):
        if not isinstance(data, bytes) or len(data) > CHUNK:
            raise ValueError("Invalid bounded chunk")
        self.buffer.extend(data)
        self.peak = max(self.peak, len(self.buffer))
        if not self.started:
            if not MAGIC.startswith(bytes(self.buffer[: len(MAGIC)])):
                raise ValueError("Invalid signature")
            if len(self.buffer) < len(MAGIC):
                return []
            del self.buffer[: len(MAGIC)]
            self.started = True
        frames = []
        while not self.ended and len(self.buffer) >= 12:
            sequence, stamp = struct.unpack_from(">IQ", self.buffer)
            if sequence == END:
                if stamp or not self.count:
                    raise ValueError("Invalid terminal record")
                del self.buffer[:12]
                self.ended = True
                break
            if not self.last < sequence < self.slots or stamp <= self.stamp:
                raise ValueError("Invalid sequence/timestamp")
            if len(self.buffer) < FRAME_BYTES + 12:
                break
            frames.append((stamp, bytes(self.buffer[12 : FRAME_BYTES + 12])))
            del self.buffer[: FRAME_BYTES + 12]
            self.last, self.stamp = sequence, stamp
            self.count += 1
        if self.ended and self.buffer:
            raise ValueError("Trailing data")
        if len(self.buffer) > FRAME_BYTES + 12:
            raise ValueError("Buffer budget exceeded")
        return frames

    def finish(self):
        if not self.started or not self.ended or self.buffer:
            raise ValueError("Truncated benchmark stream")


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return None
    return {
        "p50": ordered[(len(ordered) - 1) // 2],
        "p95": ordered[int((len(ordered) - 1) * 0.95)],
        "max": ordered[-1],
    }


class CpuSampler:
    """Approximate CPU deltas for this coordinator and its owned descendants.

    Keying by create_time avoids PID reuse. Short-lived processes or final CPU
    fractions between samples can be missed. Never signals any process.
    """

    def __init__(self):
        self.initial = {}
        self.maximum = {}
        self.sample(initial=True)

    def sample(self, *, initial=False):
        parent = psutil.Process()
        for process in [parent, *parent.children(recursive=True)]:
            try:
                key = (process.pid, process.create_time(), process.name())
                usage = process.cpu_times()
                value = usage.user + usage.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if initial:
                self.initial[key] = value
            self.maximum[key] = max(self.maximum.get(key, 0), value)

    def result(self, elapsed):
        by_name = {}
        for key, maximum in self.maximum.items():
            name = key[2]
            by_name[name] = by_name.get(name, 0) + max(
                0, maximum - self.initial.get(key, 0)
            )
        total = sum(by_name.values())
        return {
            "approximate": True,
            "seconds": total,
            "one_core_percent": 100 * total / elapsed,
            "by_process_name_seconds": by_name,
            "includes_observer": True,
        }


def collect_timed(process, on_frame, *, fps, timeout=40, cancel=None):
    decoder = TimedDecoder(fps)
    started = time.monotonic()
    deadline = started + timeout
    cpu = CpuSampler()
    sampled = started
    received, latency = [], []
    previous = None
    changed = 0
    with selectors.DefaultSelector() as selected:
        selected.register(process.stdout, selectors.EVENT_READ)
        while True:
            if cancel is not None and cancel.is_set():
                raise InterruptedError("Pixel measurement cancelled")
            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError("Benchmark stream deadline")
            if now - sampled >= 0.25:
                cpu.sample()
                sampled = now
            if not selected.select(min(deadline - now, 0.05)):
                continue
            data = os.read(process.stdout.fileno(), CHUNK)
            if not data:
                decoder.finish()
                break
            for stamp, frame in decoder.feed(data):
                arrived = time.monotonic_ns()
                delay = (arrived - stamp) / 1e6
                if delay < 0 or delay > timeout * 1000:
                    raise ValueError("Unusable capture timestamp")
                latency.append(delay)
                received.append(arrived / 1e9)
                digest = hashlib.sha256(frame).digest()
                changed += previous is not None and previous != digest
                previous = digest
                on_frame(frame)
    elapsed = time.monotonic() - started
    if elapsed < DURATION - 2:
        raise ValueError("Benchmark ended before measurement window")
    cpu.sample()
    return {
        "frames": decoder.count,
        "peak_buffer_bytes": decoder.peak,
        "requested_fps": fps,
        "measurement_seconds": elapsed,
        "nominal_window_seconds": DURATION,
        "missed_slots": decoder.slots - decoder.count,
        "delivered_per_nominal_second": decoder.count / DURATION,
        "changed_frame_transitions": changed,
        "changed_frames_per_nominal_second": changed / DURATION,
        "receive_interval_ms": distribution(
            [(b - a) * 1000 for a, b in zip(received, received[1:])]
        ),
        "capture_to_receive_ms": distribution(latency),
        "cpu_tree": cpu.result(elapsed),
        "visible_ui_latency_measured": False,
        "renderer_fps_instrumented": False,
    }


def run(root, output):
    results = {}
    for fps in (30, 60):
        directory = output / f"fps-{fps}"
        directory.mkdir(mode=0o700)
        command = [
            "/usr/bin/unshare",
            "--user",
            "--map-current-user",
            "--keep-caps",
            "--net",
            "--fork",
            "--kill-child=KILL",
            str(root / ".venv/bin/python"),
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            str(Path(__file__).with_name("projectm_pixel_probe.py").resolve()),
            "--benchmark-worker",
            str(root),
            str(directory),
            os.readlink("/proc/self/ns/net"),
            str(fps),
        ]
        print(f"Private {fps} FPS / 30 s measurement: {directory}", flush=True)
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                env={
                    "PATH": "/usr/bin:/bin",
                    "LC_ALL": "C.UTF-8",
                    "HOME": "/nonexistent",
                    "PYTHONPYCACHEPREFIX": "/nonexistent",
                },
                capture_output=True,
                text=True,
                timeout=90,
            )
        except subprocess.TimeoutExpired as exc:

            def as_text(value):
                return (
                    value.decode(errors="replace")
                    if isinstance(value, bytes)
                    else value or ""
                )

            (directory / "coordinator.log").write_text(
                as_text(exc.stdout) + as_text(exc.stderr)
            )
            results[str(fps)] = {"status": "failed", "reason": "coordinator timeout"}
        else:
            (directory / "coordinator.log").write_text(
                completed.stdout + completed.stderr
            )
            path = directory / "projectm-pixel-result.json"
            result = (
                json.loads(path.read_text()) if path.exists() else {"status": "failed"}
            )
            results[str(fps)] = {
                "status": result["status"],
                "returncode": completed.returncode,
                "transport": result.get("transport"),
                "error": result.get("error"),
            }
        print(json.dumps(results[str(fps)], indent=2), flush=True)
    (output / "benchmark-result.json").write_text(json.dumps(results, indent=2) + "\n")
    return int(
        any(
            r["status"] != "passed" or r.get("returncode") != 0
            for r in results.values()
        )
    )
