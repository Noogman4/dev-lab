"""Visualizer EQ DSP: the renderer's own Biquad/EqControl structs, compiled in a harness.

Harness approach follows Codex' review of 2026-11-11 (EQ-1). The structs are taken
verbatim from pcm_renderer.cpp, so the test always checks the shipped source.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from netmon.core import projectm_profile as profiles

ROOT = Path(__file__).resolve().parents[1]
GXX = shutil.which("g++")
pytestmark = pytest.mark.skipif(GXX is None, reason="g++ not available")

MAIN = r"""
void setting(EqControl& eq, int bass, int treble, int sens) {
    std::array<unsigned char, 8> r{static_cast<unsigned char>(bass),
        static_cast<unsigned char>(treble), static_cast<unsigned char>(sens), 1, 0, 0, 0, 0};
    for (int i = 0; i < 4; ++i) r[i + 4] = r[i] ^ 255;
    if (pwrite(eq.descriptor, r.data(), 8, 0) != 8 || !eq.update()) std::exit(2);
}
double replay_peak(EqControl& eq, int bass, int treble) {
    // Excite, go neutral, feed silence, re-enable: no stored signal may replay.
    setting(eq, bass, treble, 0);
    for (int i = 0; i < 4096; ++i) { float s[]{0.5f, 0.5f}; eq.apply(s, 2); }
    setting(eq, bass ? 0 : bass, treble ? 0 : treble, 0);
    for (int i = 0; i < 48000; ++i) { float s[]{0, 0}; eq.apply(s, 2); }
    setting(eq, bass, treble, 0);
    double peak = 0;
    for (int i = 0; i < 4800; ++i) {
        float s[]{0, 0}; eq.apply(s, 2);
        peak = std::max(peak, std::abs(double(s[0])));
    }
    return peak;
}
int main(int argc, char** argv) {
    if (argc < 3) return 2;
    EqControl eq;
    eq.descriptor = ::open(argv[1], O_RDWR | O_CLOEXEC);
    if (!eq.update()) return 2;
    std::string mode = argv[2];
    if (mode == "replay") {
        std::cout << "{\"bass\":" << replay_peak(eq, 12, 0)
                  << ",\"treble\":" << replay_peak(eq, 0, 12) << "}\n";
        // Bass toggles while treble stays active: only bass history is cleared.
        setting(eq, 12, 6, 0);
        for (int i = 0; i < 4096; ++i) { float s[]{0.5f, 0.5f}; eq.apply(s, 2); }
        setting(eq, 0, 6, 0);
        for (int i = 0; i < 48000; ++i) { float s[]{0, 0}; eq.apply(s, 2); }
        setting(eq, 12, 6, 0);
        double peak = 0;
        for (int i = 0; i < 4800; ++i) { float s[]{0, 0}; eq.apply(s, 2);
            peak = std::max(peak, std::abs(double(s[0]))); }
        std::cout << "{\"mixed\":" << peak << "}\n";
    } else if (mode == "tone") {
        setting(eq, std::stoi(argv[4]), std::stoi(argv[5]), std::stoi(argv[6]));
        double freq = std::stod(argv[3]), in = 0, out = 0;
        for (int n = 0; n < 48000; ++n) {
            float s[2]{static_cast<float>(0.01 * std::sin(2 * 3.141592653589793 * freq * n / 48000)), 0};
            double x = s[0]; eq.apply(s, 2);
            if (n >= 24000) { in += x * x; out += double(s[0]) * s[0]; }
        }
        std::cout << "{\"db\":" << 10 * std::log10(out / in) << "}\n";
    } else return 2;
}
"""


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    directory = tmp_path_factory.mktemp("eq-dsp")
    source = (ROOT / "netmon/native/projectm_pcm/pcm_renderer.cpp").read_text()
    structs = source[source.index("struct Biquad {") : source.index("int stream(")]
    prefix = "".join(
        f"#include <{name}>\n"
        for name in (
            "algorithm",
            "array",
            "cerrno",
            "cmath",
            "cstdlib",
            "fcntl.h",
            "iostream",
            "string",
            "sys/stat.h",
            "unistd.h",
        )
    )
    cpp = directory / "harness.cpp"
    cpp.write_text(prefix + structs + MAIN)
    binary = directory / "harness"
    subprocess.run(
        [
            GXX,
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(cpp),
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return binary


def run(harness, tmp_path, *args):
    record = tmp_path / "record"
    record.write_bytes(profiles.encode_visual_eq(profiles.NEUTRAL_EQ))
    os.chmod(record, 0o600)
    result = subprocess.run(
        [str(harness), str(record), *map(str, args)],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return [json.loads(line) for line in result.stdout.splitlines()]


def test_reenabling_a_shelf_after_neutral_silence_replays_nothing(harness, tmp_path):
    single, mixed = run(harness, tmp_path, "replay")
    assert single["bass"] < 1e-6 and single["treble"] < 1e-6
    assert mixed["mixed"] < 1e-3  # active treble keeps its own (silent) state


@pytest.mark.parametrize(
    "freq,bass,treble,sens,expected",
    [
        (20, 12, 0, 0, 12.0),
        (20, -12, 0, 0, -12.0),
        (150, 12, 0, 0, 6.0),
        (16000, 0, 12, 0, 12.0),
        (4000, 0, -12, 0, -6.0),
        (1000, 0, 0, 12, 12.0),
        (1000, 0, 0, 0, 0.0),
    ],
)
def test_shelf_and_gain_response(harness, tmp_path, freq, bass, treble, sens, expected):
    [result] = run(harness, tmp_path, "tone", freq, bass, treble, sens)
    assert abs(result["db"] - expected) < 0.6, result
