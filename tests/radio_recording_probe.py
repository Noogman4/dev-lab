"""Private-fixture encoder audit: replace only ffmpeg's executable contents."""

import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from urllib.parse import urlsplit

PAYLOAD = r"""
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <fcntl.h>
#include <sched.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>
#define PRIVATE @@PRIVATE@@
#define SIBLING @@SIBLING@@
#define ABSTRACT @@ABSTRACT@@
#define PORT @@PORT@@
#define SECRET_FD @@SECRET_FD@@
static int access_file(const char *name,int flags) {
 int fd=open(name,flags|O_CLOEXEC); if(fd<0)return 0; close(fd); return 1;
}
static int tcp(void) {
 int fd=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC,0);
 struct timeval timeout={.tv_sec=0,.tv_usec=300000};
 setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
 struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(PORT)};
 inet_pton(AF_INET,"93.184.216.34",&a.sin_addr);
 int ok=connect(fd,(struct sockaddr*)&a,sizeof(a))==0; close(fd);return ok;
}
static int abstract(void) {
 int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
 struct sockaddr_un a={.sun_family=AF_UNIX};
 memcpy(a.sun_path+1,ABSTRACT,strlen(ABSTRACT));
 int ok=connect(fd,(struct sockaddr*)&a,offsetof(struct sockaddr_un,sun_path)+1+strlen(ABSTRACT))==0;
 close(fd);return ok;
}
int main(void) {
 char sample; if(read(STDIN_FILENO,&sample,1)!=1)return 2;
 unsigned long caps=1; int nnp=0; char line[512];
 FILE *status=fopen("/proc/self/status","r");
 if(status){while(fgets(line,sizeof(line),status)){
  if(!strncmp(line,"CapEff:",7))caps=strtoul(line+7,NULL,16);
  if(!strncmp(line,"NoNewPrivs:",11))nnp=atoi(line+11);
 } fclose(status);}
 printf("{\"private\":%d,\"sibling_write\":%d,\"tcp\":%d,\"abstract\":%d,\"request\":%d,\"audio\":%d,\"control\":%d,\"inherited_fd\":%d,\"secret_env\":%d,\"new_userns\":%d,\"caps\":%lu,\"no_new_privs\":%d,\"output_write_only\":%d}",
 access_file(PRIVATE,O_RDONLY),access_file(SIBLING,O_WRONLY),tcp(),abstract(),
 access_file("/run/request.json",O_RDONLY),access_file("/run/audio/pulse",O_RDONLY),
 access_file("/run/control",O_RDONLY),fcntl(SECRET_FD,F_GETFD)!=-1,
 getenv("RADIO_RECORDING_FAKE_KEY")!=NULL,unshare(CLONE_NEWUSER)==0,caps,nnp,
 (fcntl(STDOUT_FILENO,F_GETFL)&O_ACCMODE)==O_WRONLY);
 fflush(stdout);
 FILE *progress=fopen("/run/record-progress","w"); if(!progress)return 2;
 fprintf(progress,"out_time_us=100000\ntotal_size=100\nprogress=end\n");
 fflush(progress); usleep(300000); fclose(progress);
 return 0;
}
"""


def audit(sandbox, output, source_url):
    compiler = shutil.which("cc")
    if not compiler:
        raise RuntimeError("Existing C compiler needed; do not install automatically")
    private = output / "recording-private-key"
    private.write_text("SYNTHETIC PRIVATE DATA")
    sibling = output / "recording-sibling"
    sibling.write_text("KEEP")
    abstract_name = "recording-" + output.name
    code = (
        PAYLOAD.replace("@@PRIVATE@@", json.dumps(str(private)))
        .replace("@@SIBLING@@", json.dumps(str(sibling)))
        .replace("@@ABSTRACT@@", json.dumps(abstract_name))
        .replace("@@PORT@@", str(urlsplit(source_url).port))
    )
    source = output / "recording-policy.c"
    binary = output / "recording-policy"
    old_environment = os.environ.get("RADIO_RECORDING_FAKE_KEY")
    with (
        private.open("rb") as secret,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
    ):
        fd = fcntl.fcntl(secret.fileno(), fcntl.F_DUPFD, 200)
        os.set_inheritable(fd, True)
        listener.bind("\0" + abstract_name)
        listener.listen(2)
        source.write_text(code.replace("@@SECRET_FD@@", str(fd)))
        result = subprocess.run(
            [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(source),
                "-o",
                str(binary),
            ],
            env=sandbox._ENV,
            capture_output=True,
            text=True,
            timeout=20,
        )
        (output / "recording-compile.log").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, "recording audit compilation failed"
        assert {p.resolve() for p in sandbox._runtime_files(binary)} - {
            binary.resolve()
        } <= {p.resolve() for p in sandbox._runtime_files(sandbox.FFMPEG)}
        original = sandbox._sandbox_command

        def substitute(command, *args, **kwargs):
            plan = original(command, *args, **kwargs)
            if command[0] == str(sandbox.FFMPEG):
                for i in range(len(plan) - 2):
                    if plan[i] == "--ro-bind" and plan[i + 2] == str(sandbox.FFMPEG):
                        plan[i + 1] = str(binary)
            return plan

        os.environ["RADIO_RECORDING_FAKE_KEY"] = "SYNTHETIC KEY"
        sandbox._sandbox_command = substitute
        try:
            proc = sandbox.start_recording(
                source_url, output / "recording-policy-report.mp3", work_root=output
            )
            proc.terminate()
            assert proc.wait(timeout=3) == 0
            report = json.loads(Path(proc.output_path).read_text())
        finally:
            sandbox._sandbox_command = original
            os.close(fd)
            if old_environment is None:
                os.environ.pop("RADIO_RECORDING_FAKE_KEY", None)
            else:
                os.environ["RADIO_RECORDING_FAKE_KEY"] = old_environment
    assert all(
        report[name] == 0
        for name in (
            "private",
            "sibling_write",
            "tcp",
            "abstract",
            "request",
            "audio",
            "control",
            "inherited_fd",
            "secret_env",
            "new_userns",
            "caps",
        )
    ), report
    assert report["no_new_privs"] == report["output_write_only"] == 1, report
    assert sibling.read_text() == "KEEP"
    return report
