// NetMon version-bound projectM 3.1.13 PCM renderer. No audio-server client.
#include "projectM.hpp"
#ifdef NETMON_EGL
#include "egl_context.hpp"
#include <cstdlib>
#else
#include <X11/Xlib.h>
#include <GL/glx.h>
#endif
#include <algorithm>
#include <array>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <poll.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#include <thread>
#include <unordered_map>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
constexpr size_t Bytes = 4096;
struct Profile { const char* key; int width, height; };
constexpr std::array<Profile, 4> Profiles{{
    {"640x480", 640, 480}, {"960x540", 960, 540},
    {"1280x720", 1280, 720}, {"1920x1080", 1920, 1080}
}};

bool limit(int name, rlim_t maximum) {
    rlimit bound{};
    if (getrlimit(name, &bound)) return false;
    if (bound.rlim_cur != RLIM_INFINITY) maximum = std::min(maximum, bound.rlim_cur);
    if (bound.rlim_max != RLIM_INFINITY) maximum = std::min(maximum, bound.rlim_max);
    bound.rlim_cur = bound.rlim_max = maximum;
    return setrlimit(name, &bound) == 0;
}

#ifdef NETMON_EGL
struct WindowOwner : EglContext {
    int width = 0, height = 0;
    bool announced = false;
    std::string key;
    std::vector<unsigned char> pixels;
    bool create(const Profile& profile) {
        width = profile.width;
        height = profile.height;
        key = profile.key;
        pixels.resize(static_cast<size_t>(width) * height * 4);
        return EglContext::create(std::getenv("NETMON_GPU_NODE"), width, height);
    }
    bool events() { return true; }
    static bool write_all(int fd, const unsigned char* data, size_t size) {
        while (size) {
            const ssize_t written = write(fd, data, size);
            if (written < 0 && errno == EINTR) continue;
            if (written <= 0) return false;
            data += written;
            size -= static_cast<size_t>(written);
        }
        return true;
    }
    bool present(int output) {
        glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
        if (glGetError() != GL_NO_ERROR) return false;
        if (!announced) {
            const std::string marker = "NMPG1 " + key + "\n";
            if (!write_all(output, reinterpret_cast<const unsigned char*>(marker.data()), marker.size())) return false;
            announced = true;
        }
        // OpenGL's bottom row becomes the final row in the trusted RGBA stream.
        const size_t stride = static_cast<size_t>(width) * 4;
        for (int row = height - 1; row >= 0; --row) {
            if (!write_all(output, pixels.data() + row * stride, stride)) return false;
        }
        return true;
    }
};
#else
struct WindowOwner {
    Display* display = nullptr;
    Window window = 0;
    Colormap colors = 0;
    GLXContext context = nullptr;
    ~WindowOwner() {
        if (!display) return;
        glXMakeCurrent(display, 0, nullptr);
        if (context) glXDestroyContext(display, context);
        if (window) XDestroyWindow(display, window);
        if (colors) XFreeColormap(display, colors);
        XCloseDisplay(display);
    }
    bool create(const Profile& profile) {
        display = XOpenDisplay(":1");
        if (!display) return false;
        int attributes[] = {GLX_RGBA, GLX_DOUBLEBUFFER, GLX_RED_SIZE, 8,
                            GLX_GREEN_SIZE, 8, GLX_BLUE_SIZE, 8, None};
        XVisualInfo* visual = glXChooseVisual(display, DefaultScreen(display), attributes);
        if (!visual) return false;
        colors = XCreateColormap(display, RootWindow(display, visual->screen), visual->visual, AllocNone);
        XSetWindowAttributes attrs{};
        attrs.colormap = colors;
        attrs.event_mask = StructureNotifyMask | ExposureMask;
        window = XCreateWindow(display, RootWindow(display, visual->screen), 0, 0,
                               profile.width, profile.height, 0, visual->depth, InputOutput, visual->visual,
                               CWColormap | CWEventMask, &attrs);
        context = glXCreateContext(display, visual, nullptr, True);
        XFree(visual);
        if (!context || !window) return false;
        XMapWindow(display, window);
        XSync(display, False);
        return glXMakeCurrent(display, window, context);
    }
    bool events() {
        for (int i = 0; i < 16 && XPending(display); ++i) {
            XEvent event{};
            XNextEvent(display, &event);
            if (event.type == DestroyNotify) return false;
        }
        return true;
    }
    bool present(int) { glXSwapBuffers(display, window); return true; }
};
#endif

struct PresetControl {
    int descriptor = -1;
    uint32_t last = UINT32_MAX;
    std::vector<unsigned int> indices;
    ~PresetControl() { if (descriptor >= 0) close(descriptor); }
    bool open(projectM& engine) {
        struct stat info{};
        if (stat("/media/preset-list", &info) || !S_ISREG(info.st_mode) ||
            info.st_size > 4 * 1024 * 1024) return false;
        std::ifstream input("/media/preset-list");
        std::vector<std::string> urls;
        std::string name;
        while (std::getline(input, name)) {
            if (name.size() != 69 || urls.size() >= 50000 ||
                (name.substr(64) != ".milk" && name.substr(64) != ".prjm") ||
                !std::all_of(name.begin(), name.begin() + 64, [](char c) {
                    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
                })) return false;
            urls.push_back("/media/playlist/" + name);
        }
        if (!input.eof() || urls.empty()) return false;
        if (engine.getPlaylistSize() > 50000) return false;
        // This library's getPresetIndex() did not resolve these exact URLs.
        // Resolve once using exact URLs; later selections are constant-time.
        std::unordered_map<std::string, unsigned int> playlist;
        for (unsigned int i = 0; i < engine.getPlaylistSize(); ++i) {
            playlist.emplace(engine.getPresetURL(i), i);
        }
        for (const auto& url : urls) {
            const auto found = playlist.find(url);
            if (found == playlist.end()) return false;
            indices.push_back(found->second);
        }
        descriptor = ::open("/run/preset-selection", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
        return descriptor >= 0 && !fstat(descriptor, &info) &&
               S_ISREG(info.st_mode) && info.st_size == 8;
    }
    bool update(projectM& engine) {
        std::array<unsigned char, 8> record{};
        const auto count = pread(descriptor, record.data(), record.size(), 0);
        if (count < 0 && errno == EINTR) return true;
        if (count != 8) return false;
        uint32_t index = 0, inverse = 0;
        for (int i = 0; i < 4; ++i) {
            index = (index << 8) | record[i];
            inverse = (inverse << 8) | record[i + 4];
        }
        // A concurrent replacement is ignored until a complete record is seen.
        if ((index ^ inverse) != UINT32_MAX || index == last) return true;
        if (index == UINT32_MAX) {
            engine.setPresetLock(false);
        } else {
            if (index >= indices.size()) return false;
            engine.selectPreset(indices[index], true);
            engine.setPresetLock(true);
        }
        last = index;
        return true;
    }
};

// Visualizer-only EQ (bass/treble shelves, overall gain) on the PCM copy that
// projectM analyses. Fixed 8-byte record: bass, treble, sensitivity (int8 dB),
// version 1, then the bitwise complement. Neutral values leave samples untouched.
struct Biquad {
    double b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
    double z1[2]{}, z2[2]{};
    // RBJ audio-EQ cookbook shelf, slope 1, fs 48 kHz.
    void shelf(bool low, double freq, double gain_db) {
        const double A = std::pow(10.0, gain_db / 40.0);
        const double w = 2.0 * 3.14159265358979323846 * freq / 48000.0;
        const double c = std::cos(w), alpha = std::sin(w) / 2.0 * std::sqrt(2.0);
        const double r = 2.0 * std::sqrt(A) * alpha;
        double nb0, nb1, nb2, na0, na1, na2;
        if (low) {
            nb0 = A * ((A + 1) - (A - 1) * c + r);
            nb1 = 2 * A * ((A - 1) - (A + 1) * c);
            nb2 = A * ((A + 1) - (A - 1) * c - r);
            na0 = (A + 1) + (A - 1) * c + r;
            na1 = -2 * ((A - 1) + (A + 1) * c);
            na2 = (A + 1) + (A - 1) * c - r;
        } else {
            nb0 = A * ((A + 1) + (A - 1) * c + r);
            nb1 = -2 * A * ((A - 1) + (A + 1) * c);
            nb2 = A * ((A + 1) + (A - 1) * c - r);
            na0 = (A + 1) - (A - 1) * c + r;
            na1 = 2 * ((A - 1) - (A + 1) * c);
            na2 = (A + 1) - (A - 1) * c - r;
        }
        b0 = nb0 / na0; b1 = nb1 / na0; b2 = nb2 / na0; a1 = na1 / na0; a2 = na2 / na0;
    }
    // Skipped while neutral: history from before must not replay on re-enable.
    void reset() { z1[0] = z1[1] = z2[0] = z2[1] = 0.0; }
    float run(int ch, float x) {
        const double y = b0 * x + z1[ch];
        z1[ch] = b1 * x - a1 * y + z2[ch];
        z2[ch] = b2 * x - a2 * y;
        return static_cast<float>(y);
    }
};

struct EqControl {
    int descriptor = -1;
    int bass = 0, treble = 0, sensitivity = 0;
    double gain = 1.0;
    Biquad low, high;
    ~EqControl() { if (descriptor >= 0) close(descriptor); }
    bool open() {
        struct stat info{};
        descriptor = ::open("/run/visual-eq", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
        return descriptor >= 0 && !fstat(descriptor, &info) &&
               S_ISREG(info.st_mode) && info.st_size == 8;
    }
    bool update() {
        std::array<unsigned char, 8> record{};
        const auto count = pread(descriptor, record.data(), record.size(), 0);
        if (count < 0 && errno == EINTR) return true;
        if (count != 8) return false;
        for (int i = 0; i < 4; ++i) {
            // A concurrent replacement is ignored until a complete record is seen.
            if ((record[i] ^ record[i + 4]) != 0xFF) return true;
        }
        if (record[3] != 1) return false;
        const int values[3] = {static_cast<signed char>(record[0]),
                               static_cast<signed char>(record[1]),
                               static_cast<signed char>(record[2])};
        for (int value : values) if (value < -12 || value > 12) return false;
        if (values[0] != bass) {
            if (!values[0] || !bass) low.reset();
            bass = values[0];
            low.shelf(true, 150.0, bass);
        }
        if (values[1] != treble) {
            if (!values[1] || !treble) high.reset();
            treble = values[1];
            high.shelf(false, 4000.0, treble);
        }
        if (values[2] != sensitivity) {
            sensitivity = values[2];
            gain = std::pow(10.0, sensitivity / 20.0);
        }
        return true;
    }
    void apply(float* samples, size_t count) {
        if (!bass && !treble && !sensitivity) return;
        for (size_t i = 0; i < count; ++i) {
            const int ch = static_cast<int>(i & 1);
            float x = samples[i];
            if (bass) x = low.run(ch, x);
            if (treble) x = high.run(ch, x);
            samples[i] = static_cast<float>(x * gain);
        }
    }
};

int stream(projectM& engine, WindowOwner& graphics, PresetControl& control, EqControl& eq, int status, int fps) {
    std::array<float, Bytes / sizeof(float)> pcm{};
    size_t used = 0, blocks = 0;
    bool ready = false, eof = false;
    auto last_complete = Clock::now();
    auto consume = [&](size_t size) {
        if (!size || size % (2 * sizeof(float))) return false;
        const size_t count = size / sizeof(float);
        for (size_t i = 0; i < count; ++i) {
            if (!std::isfinite(pcm[i])) return false;
            pcm[i] = std::clamp(pcm[i], -1.0f, 1.0f);
        }
        eq.apply(pcm.data(), count);
        for (size_t i = 0; i < count; ++i) {
            if (!std::isfinite(pcm[i])) return false;
            pcm[i] = std::clamp(pcm[i], -1.0f, 1.0f);
        }
        engine.pcm()->addPCMfloat_2ch(pcm.data(), count);
        ++blocks;
        return true;
    };
    while (true) {
        const auto next_tick = Clock::now() + std::chrono::nanoseconds(1000000000 / fps);
        if (!control.update(engine) || !eq.update()) return 4;
        if (Clock::now() - last_complete >= std::chrono::seconds(5)) return 3;
        // X requests and audio bursts are bounded per tick.
        if (!graphics.events()) return 4;
        for (int budget = 0; budget < 4; ++budget) {
            ssize_t count = read(STDIN_FILENO, reinterpret_cast<char*>(pcm.data()) + used, Bytes - used);
            if (count < 0) {
                if (errno == EINTR) continue;
                if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                return 4;
            }
            if (!count) {
                eof = true;
                if (used && !consume(used)) return 2;
                break;
            }
            used += static_cast<size_t>(count);
            if (used == Bytes) {
                if (!consume(used)) return 2;
                used = 0;
                last_complete = Clock::now();
            }
        }
        if (blocks) {
            engine.renderFrame();
            if (!graphics.present(status)) return 4;
            if (!ready) {
#ifndef NETMON_EGL
                constexpr char message[] = "NMPM1 READY\n";
                if (write(status, message, sizeof(message) - 1) != sizeof(message) - 1) return 4;
#endif
                ready = true;
            }
        }
        if (eof) {
            std::fprintf(stderr, "PCM-END blocks=%zu tail=%zu\n", blocks, used);
            return ready ? 0 : 2;
        }
        // One loop is one render tick, including partial-read and flood cases.
        // Sub-millisecond rounding must never reset the four-block budget.
        std::this_thread::sleep_until(next_tick);
    }
}
}  // namespace

int main(int argc, char** argv) {
    const Profile* profile = nullptr;
    const std::string key = argc == 1 ? "640x480" : argc <= 3 ? argv[1] : "";
    const std::string cpu = argc <= 2 ? "standard" : argc == 3 ? argv[2] : "";
    const int fps = cpu == "standard" ? 25 : cpu == "performance" ? 30 : 0;
    for (const auto& item : Profiles) if (key == item.key) profile = &item;
    if (!profile || !fps || !limit(RLIMIT_AS, 2ULL * 1024 * 1024 * 1024) ||
        !limit(RLIMIT_FSIZE, 16ULL * 1024 * 1024) || !limit(RLIMIT_NOFILE, 256)) return 4;
    umask(0077);
    int status = fcntl(STDOUT_FILENO, F_DUPFD_CLOEXEC, 3);
    if (status < 0 || dup2(STDERR_FILENO, STDOUT_FILENO) < 0) return 4;
    int flags = fcntl(STDIN_FILENO, F_GETFL);
    if (flags < 0 || fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK)) return 4;
    std::cout.rdbuf(std::cerr.rdbuf());
    int result = 4;
    try {
        WindowOwner graphics;
        if (graphics.create(*profile)) {
            projectM engine(std::string("/media/config.inp"), projectM::FLAG_NONE);
            engine.projectM_resetGL(profile->width, profile->height);
            engine.selectPreset(0, true);
            PresetControl control;
            EqControl eq;
            if (control.open(engine) && eq.open() && eq.update()) {
                result = stream(engine, graphics, control, eq, status, fps);
            }
        }
    } catch (...) {
        result = 4;
    }
    close(status);
    return result;
}
