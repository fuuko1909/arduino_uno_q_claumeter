#include "data.h"

size_t safe_strlcpy(char* dst, const char* src, size_t size) {
    if (size == 0) return 0;
    size_t i = 0;
    while (i + 1 < size && src[i] != '\0') {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\0';
    while (src[i] != '\0') i++;
    return i;
}
