// Desktop OpenGL on one explicitly selected EGL DRM render node; no desktop.
#pragma once
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/gl.h>
#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <string>
#include <sys/stat.h>

struct EglContext {
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLSurface surface = EGL_NO_SURFACE;
    EGLContext context = EGL_NO_CONTEXT;
    std::string renderer;
    ~EglContext() {
        if (display == EGL_NO_DISPLAY) return;
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        if (context != EGL_NO_CONTEXT) eglDestroyContext(display, context);
        if (surface != EGL_NO_SURFACE) eglDestroySurface(display, surface);
        eglTerminate(display);
    }
    static bool extension(const char* list, const char* name) {
        if (!list) return false;
        const std::string tokens = " " + std::string(list) + " ";
        return tokens.find(" " + std::string(name) + " ") != std::string::npos;
    }
    bool create(const char* node, int width, int height) {
        struct stat expected{};
        if (!node || std::strlen(node) > 64 || stat(node, &expected) || !S_ISCHR(expected.st_mode)) return false;
        auto enumerate = reinterpret_cast<PFNEGLQUERYDEVICESEXTPROC>(eglGetProcAddress("eglQueryDevicesEXT"));
        auto query = reinterpret_cast<PFNEGLQUERYDEVICESTRINGEXTPROC>(eglGetProcAddress("eglQueryDeviceStringEXT"));
        auto platform = reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));
        if (!enumerate || !query || !platform) return false;
        if (!extension(eglQueryString(EGL_NO_DISPLAY, EGL_EXTENSIONS), "EGL_EXT_platform_device")) return false;
        std::array<EGLDeviceEXT, 16> devices{};
        EGLint count = 0;
        if (!enumerate(devices.size(), devices.data(), &count) || count < 1 || count > 16) return false;
        EGLDeviceEXT selected = nullptr;
        for (int i = 0; i < count; ++i) {
            if (!extension(query(devices[i], EGL_EXTENSIONS), "EGL_EXT_device_drm_render_node")) continue;
            const char* path = query(devices[i], EGL_DRM_RENDER_NODE_FILE_EXT);
            std::fprintf(stderr, "EGL_DEVICE %s\n", path ? path : "none");
            if (path && std::strcmp(path, node) == 0) {
                if (selected) return false;
                selected = devices[i];
            }
        }
        if (!selected) return false;
        display = platform(EGL_PLATFORM_DEVICE_EXT, selected, nullptr);
        EGLint major = 0, minor = 0;
        if (display == EGL_NO_DISPLAY || !eglInitialize(display, &major, &minor) || !eglBindAPI(EGL_OPENGL_API)) return false;
        const EGLint attributes[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE};
        EGLConfig config = nullptr;
        EGLint found = 0;
        if (!eglChooseConfig(display, attributes, &config, 1, &found) || found != 1) return false;
        const EGLint size[] = {EGL_WIDTH, width, EGL_HEIGHT, height, EGL_NONE};
        surface = eglCreatePbufferSurface(display, config, size);
        const EGLint version[] = {EGL_CONTEXT_MAJOR_VERSION_KHR, 3, EGL_CONTEXT_MINOR_VERSION_KHR, 3,
            EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR, EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT_KHR, EGL_NONE};
        context = eglCreateContext(display, config, EGL_NO_CONTEXT, version);
        if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT || !eglMakeCurrent(display, surface, surface, context)) return false;
        const char* text = reinterpret_cast<const char*>(glGetString(GL_RENDERER));
        if (!text || std::strlen(text) > 1024) return false;
        renderer = text;
        std::string lower = renderer;
        std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return std::tolower(c); });
        if (lower.find("llvmpipe") != std::string::npos || lower.find("softpipe") != std::string::npos ||
            lower.find("software") != std::string::npos) return false;
        // Corroborate the renderer string with an actually open FD to the selected device.
        bool device_open = false;
        DIR* directory = opendir("/proc/self/fd");
        if (!directory) return false;
        while (auto* entry = readdir(directory)) {
            struct stat info{};
            const std::string path = "/proc/self/fd/" + std::string(entry->d_name);
            if (!stat(path.c_str(), &info) && S_ISCHR(info.st_mode) && info.st_rdev == expected.st_rdev) device_open = true;
        }
        closedir(directory);
        std::fprintf(stderr, "GPU_CONTEXT node=%s renderer=%s version=%s device_fd=%d\n", node, renderer.c_str(), glGetString(GL_VERSION), device_open);
        return device_open;
    }
};
