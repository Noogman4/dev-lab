"""Adversarial policy probes: synthetic data and private test services only.

The compiled fixture replaces mpv's executable contents for this test. All path
grants, namespaces, environment construction and start_playback/close_fds remain
those of the real policy. Its dynamic libraries must be a subset of mpv's own
runtime. This models code execution in a compromised decoder, not an mpv exploit.
"""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
from urllib.parse import urlsplit

PAYLOAD = r"""
#include <errno.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>
#include <pulse/pulseaudio.h>

#define PRIVATE_PATH @@PRIVATE@@
#define ABSTRACT_NAME @@NAME@@
#define SECRET_FD @@FD@@
#define TCP_PORT @@PORT@@

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1000000000.0;
}

static int readable(const char *path) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return 0;
    close(fd);
    return 1;
}

static int writable(const char *path) {
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) return 0;
    close(fd);
    return 1;
}

static int abstract_service(void) {
    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    struct sockaddr_un address = { .sun_family = AF_UNIX };
    struct timeval timeout = { .tv_sec = 0, .tv_usec = 300000 };
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    memcpy(address.sun_path + 1, ABSTRACT_NAME, strlen(ABSTRACT_NAME));
    int ok = connect(fd, (struct sockaddr *)&address,
        offsetof(struct sockaddr_un, sun_path) + 1 + strlen(ABSTRACT_NAME)) == 0;
    char reply = 0;
    if (ok) ok = recv(fd, &reply, 1, 0) == 1 && reply == 'R';
    close(fd);
    return ok;
}

static int tcp_service(void) {
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    struct sockaddr_in address = { .sin_family = AF_INET, .sin_port = htons(TCP_PORT) };
    struct timeval timeout = { .tv_sec = 0, .tv_usec = 300000 };
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    inet_pton(AF_INET, "93.184.216.34", &address.sin_addr);
    int ok = connect(fd, (struct sockaddr *)&address, sizeof(address)) == 0;
    close(fd);
    return ok;
}

static void audio_capture(int *context_ready, int *record_ready, size_t *bytes, int *error) {
    pa_mainloop *loop = pa_mainloop_new();
    pa_context *context = pa_context_new(pa_mainloop_get_api(loop), "netmon-security-probe");
    pa_stream *stream = NULL;
    if (pa_context_connect(context, "unix:/run/audio/pulse", PA_CONTEXT_NOAUTOSPAWN, NULL) < 0) goto done;
    double end = now() + 1.2;
    while (now() < end) {
        pa_mainloop_iterate(loop, 0, NULL);
        pa_context_state_t state = pa_context_get_state(context);
        if (state == PA_CONTEXT_READY) { *context_ready = 1; break; }
        if (!PA_CONTEXT_IS_GOOD(state)) goto done;
        usleep(2000);
    }
    if (!*context_ready) goto done;
    pa_sample_spec sample = { .format = PA_SAMPLE_S16LE, .rate = 8000, .channels = 1 };
    stream = pa_stream_new(context, "synthetic-monitor-capture", &sample, NULL);
    if (pa_stream_connect_record(stream, "netmon_test.monitor", NULL, PA_STREAM_NOFLAGS) < 0) goto done;
    end = now() + 1.2;
    while (now() < end) {
        pa_mainloop_iterate(loop, 0, NULL);
        pa_stream_state_t state = pa_stream_get_state(stream);
        if (state == PA_STREAM_READY) *record_ready = 1;
        if (!PA_STREAM_IS_GOOD(state)) break;
        if (*record_ready && pa_stream_readable_size(stream) > 0) {
            const void *data = NULL;
            size_t count = 0;
            if (pa_stream_peek(stream, &data, &count) == 0) {
                *bytes = count;
                pa_stream_drop(stream);
                break;
            }
        }
        usleep(2000);
    }
done:
    *error = pa_context_errno(context);
    if (stream) { pa_stream_disconnect(stream); pa_stream_unref(stream); }
    pa_context_disconnect(context);
    pa_context_unref(context);
    pa_mainloop_free(loop);
}

int main(void) {
    struct stat inherited;
    int fd_open = fstat(SECRET_FD, &inherited) == 0;
    int private_read = readable(PRIVATE_PATH);
    symlink(PRIVATE_PATH, "/tmp/escape");
    int symlink_read = readable("/tmp/escape");
    int proc_read = readable("/proc/1/root" PRIVATE_PATH);
    int selected_write = writable("/media/selected");
    int selected_read = readable("/media/selected");
    int userns = unshare(CLONE_NEWUSER) == 0;
    int userns_errno = errno;
    int no_new_privs = -1;
    unsigned long long capabilities = 1;
    FILE *status = fopen("/proc/self/status", "r");
    if (status) {
        char line[1024];
        while (fgets(line, sizeof(line), status)) {
            sscanf(line, "NoNewPrivs:%d", &no_new_privs);
            sscanf(line, "CapEff:%llx", &capabilities);
        }
        fclose(status);
    }
    int network = abstract_service();
    int context_ready = 0, record_ready = 0, error = 0;
    size_t bytes = 0;
    audio_capture(&context_ready, &record_ready, &bytes, &error);
    FILE *report = fopen("/run/control/security-report.json", "w");
    if (!report) return 2;
    fprintf(report, "{\"private_read\":%d,\"symlink_read\":%d,\"proc_root_read\":%d,"
        "\"selected_write\":%d,\"selected_read\":%d,\"inherited_fd_open\":%d,\"ambient_key\":%d,"
        "\"new_userns\":%d,\"userns_errno\":%d,\"no_new_privs\":%d,"
        "\"capabilities\":%llu,\"abstract_service\":%d,"
        "\"pulse_context\":%d,\"capture_ready\":%d,\"capture_bytes\":%zu,\"pulse_error\":%d,"
        "\"output_write_only\":%d,\"pulse_environment\":%d,\"audio_socket_present\":%d,"
        "\"tcp_service\":%d,\"source_request_visible\":%d,\"resolver_file_visible\":%d}\n",
        private_read, symlink_read, proc_read, selected_write, selected_read, fd_open,
        getenv("RADIO_SECURITY_FAKE_KEY") != NULL, userns, userns_errno,
        no_new_privs, capabilities, network, context_ready, record_ready, bytes, error,
        (fcntl(STDOUT_FILENO, F_GETFL) & O_ACCMODE) == O_WRONLY,
        getenv("PULSE_SERVER") != NULL, access("/run/audio/pulse", F_OK) == 0,
        tcp_service(), access("/run/request.json", F_OK) == 0,
        access("/etc/resolv.conf", F_OK) == 0);
    fclose(report);
    return 0;
}
"""


def audit(sandbox, output, source_url):
    compiler = shutil.which("cc")
    if not compiler or not Path("/usr/include/pulse/pulseaudio.h").is_file():
        raise RuntimeError(
            "Existing C compiler/Pulse headers required; do not install automatically"
        )
    private = output / "synthetic-private-key"
    private.write_text("SYNTHETIC-PRIVATE-DATA")
    selected = output / "selected-media"
    selected.write_text("SYNTHETIC-MEDIA")
    original_builder = sandbox._sandbox_command
    original_cleanup = sandbox.SandboxProcess._cleanup
    original_key = os.environ.get("RADIO_SECURITY_FAKE_KEY")
    reports = {}
    stop = threading.Event()
    name = "netmon-audit-" + output.name
    with (
        private.open("rb") as secret,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
    ):
        secret_fd = fcntl.fcntl(secret.fileno(), fcntl.F_DUPFD, 200)
        os.set_inheritable(secret_fd, True)
        listener.bind("\0" + name)
        listener.listen(4)
        listener.settimeout(0.1)

        def service():
            while not stop.is_set():
                try:
                    client, _address = listener.accept()
                except TimeoutError:
                    continue
                with client:
                    client.sendall(b"R")

        thread = threading.Thread(target=service, daemon=True)
        thread.start()
        try:
            code = PAYLOAD.replace("@@PRIVATE@@", json.dumps(str(private)))
            code = code.replace("@@NAME@@", json.dumps(name)).replace(
                "@@FD@@", str(secret_fd)
            )
            code = code.replace("@@PORT@@", str(urlsplit(source_url).port))
            source = output / "policy_probe.c"
            binary = output / "policy_probe"
            source.write_text(code)
            compiled = subprocess.run(
                [
                    compiler,
                    "-D_GNU_SOURCE",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    str(source),
                    "-o",
                    str(binary),
                    "-l:libpulse.so.0",
                ],
                env=sandbox._ENV,
                cwd=output,
                capture_output=True,
                text=True,
                timeout=20,
            )
            (output / "security-compile.log").write_text(
                compiled.stdout + compiled.stderr
            )
            assert (
                compiled.returncode == 0
            ), "Probe compilation failed; see security-compile.log"
            runtime = {path.resolve() for path in sandbox._runtime_files(sandbox.MPV)}
            dependencies = {
                path.resolve()
                for path in sandbox._runtime_files(binary)
                if path != binary
            }
            assert dependencies <= runtime, "Probe would require broader runtime grants"

            def replace_only_executable(*args, **kwargs):
                command = original_builder(*args, **kwargs)
                replaced = 0
                for index in range(len(command) - 2):
                    if command[index] == "--ro-bind" and command[index + 2] == str(
                        sandbox.MPV
                    ):
                        command[index + 1] = str(binary)
                        replaced += 1
                assert replaced == (
                    0
                    if kwargs.get("audio_output") or kwargs.get("network_source")
                    else 1
                )
                return command

            sandbox._sandbox_command = replace_only_executable
            os.environ["RADIO_SECURITY_FAKE_KEY"] = "SYNTHETIC"
            for local in (True, False):
                mode = "local" if local else "online"

                def collect_before_cleanup(process):
                    source = Path(process.ipc_path).parent / "security-report.json"
                    if source.exists():
                        shutil.copyfile(source, output / f"security-{mode}.log")
                    original_cleanup(process)

                sandbox.SandboxProcess._cleanup = collect_before_cleanup
                try:
                    sandbox.start_playback(
                        [
                            "mpv",
                            f"--input-ipc-server={sandbox.IPC_PATH}",
                            "--",
                            source_url,
                        ],
                        ipc_root=output / "ipc",
                        local_file=selected if local else None,
                    )
                except sandbox.RadioSandboxError:
                    # The fixture reports and exits, rather than pretending
                    # to be a ready mpv IPC server.
                    pass
                else:
                    raise AssertionError("Non-player accepted as ready mpv")
                data = json.loads((output / f"security-{mode}.log").read_text())
                reports[mode] = data
                for key in (
                    "private_read",
                    "symlink_read",
                    "proc_root_read",
                    "selected_write",
                    "inherited_fd_open",
                    "ambient_key",
                    "new_userns",
                    "capabilities",
                ):
                    assert data[key] == 0, (mode, key, data)
                assert data["no_new_privs"] == 1
                assert data["selected_read"] == int(local)
                assert data["abstract_service"] == 0
                assert data["pulse_context"] == 0
                assert data["capture_ready"] == 0
                assert data["capture_bytes"] == 0
                assert data["output_write_only"] == 1
                assert data["pulse_environment"] == 0
                assert data["audio_socket_present"] == 0
                assert data["tcp_service"] == 0
                assert data["source_request_visible"] == 0
                assert data["resolver_file_visible"] == 0
                assert not list((output / "ipc").glob("play-*"))
        finally:
            sandbox._sandbox_command = original_builder
            sandbox.SandboxProcess._cleanup = original_cleanup
            if original_key is None:
                os.environ.pop("RADIO_SECURITY_FAKE_KEY", None)
            else:
                os.environ["RADIO_SECURITY_FAKE_KEY"] = original_key
            os.close(secret_fd)
            stop.set()
            thread.join(timeout=2)
    return {
        "security_acceptance": False,
        "scope": "compromised-decoder model; executable substituted, grants unchanged",
        "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reports": reports,
        "checks": [
            "synthetic private files hidden directly, through symlink and supervisor proc root",
            "selected local media read-only; inherited secret FD and ambient key absent",
            "no new privileges, zero effective capabilities and further user namespace denied",
            "decoder has no Pulse connection or recording stream; output pipe is write-only",
            "online and local decoder cannot reach TCP or abstract Unix test services; source request and resolver files hidden",
            "fixture rejected as mpv-ready and IPC directory cleaned",
        ],
        "open_limits": [
            "trusted HTTP source retains networking; its resolver and TLS stack remain part of the trusted base",
            "trusted raw output process still owns the PulseAudio capability; it is not a server-side playback-only permission",
        ],
        "capture_data_observed": any(
            report["capture_bytes"] > 0 for report in reports.values()
        ),
        "host_services_contacted": False,
        "physical_microphone_used": False,
    }
