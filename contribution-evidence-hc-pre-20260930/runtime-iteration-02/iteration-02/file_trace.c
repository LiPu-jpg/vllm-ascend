#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

static void trace_path(const char *operation, const char *path, long result) {
    int saved_errno = errno;
    const char *destination = getenv("HC_PRE_FILE_TRACE");
    if (destination && path && (strstr(path, "HcPre") || strstr(path, "hc_pre") || strstr(path, "libcust_"))) {
        char buffer[8192];
        int count = snprintf(buffer, sizeof(buffer), "%s\t%ld\t%s\n", operation, result, path);
        if (count > 0 && count < (int)sizeof(buffer)) {
            int fd = syscall(SYS_openat, AT_FDCWD, destination, O_CREAT | O_WRONLY | O_APPEND, 0600);
            if (fd >= 0) {
                syscall(SYS_write, fd, buffer, count);
                syscall(SYS_close, fd);
            }
        }
    }
    errno = saved_errno;
}

#define DEFINE_OPEN(symbol) \
int symbol(const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if ((flags & O_CREAT) || ((flags & O_TMPFILE) == O_TMPFILE)) { \
        va_list args; va_start(args, flags); mode = va_arg(args, int); va_end(args); \
    } \
    int (*real_function)(const char *, int, ...) = dlsym(RTLD_NEXT, #symbol); \
    int result = real_function(path, flags, mode); \
    trace_path(#symbol, path, result); \
    return result; \
}
DEFINE_OPEN(open)
DEFINE_OPEN(open64)

#define DEFINE_OPENAT(symbol) \
int symbol(int dirfd, const char *path, int flags, ...) { \
    mode_t mode = 0; \
    if ((flags & O_CREAT) || ((flags & O_TMPFILE) == O_TMPFILE)) { \
        va_list args; va_start(args, flags); mode = va_arg(args, int); va_end(args); \
    } \
    int (*real_function)(int, const char *, int, ...) = dlsym(RTLD_NEXT, #symbol); \
    int result = real_function(dirfd, path, flags, mode); \
    trace_path(#symbol, path, result); \
    return result; \
}
DEFINE_OPENAT(openat)
DEFINE_OPENAT(openat64)

#define DEFINE_FOPEN(symbol) \
FILE *symbol(const char *path, const char *mode) { \
    FILE *(*real_function)(const char *, const char *) = dlsym(RTLD_NEXT, #symbol); \
    FILE *result = real_function(path, mode); \
    trace_path(#symbol, path, result ? fileno(result) : -1); \
    return result; \
}
DEFINE_FOPEN(fopen)
DEFINE_FOPEN(fopen64)
