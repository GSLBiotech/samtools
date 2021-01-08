#ifndef SAM_MSVC_H
#define SAM_MSVC_H

int mkstemp(char *tmpl);

#define popen _popen
#define pclose _pclose

#endif //SAM_MSVC_H
