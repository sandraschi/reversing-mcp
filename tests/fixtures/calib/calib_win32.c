/* calib_win32.c - hermetic calibration target #1 (real Win32, known answers).
 *
 * Known UI: menu File (Open/Save/Exit), menu Help (About); a "Write file"
 * button; an About dialog with fixed text. Known I/O: button writes
 * %TEMP%\\calib_win32_probe.txt with fixed content.
 * Expected manifest: tests/fixtures/calib/expected.json (CALIB_WIN32).
 * Build: scripts/build_calib.py (MSVC cl.exe) or just calib.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>

#define IDM_OPEN 101
#define IDM_SAVE 102
#define IDM_EXIT 103
#define IDM_ABOUT 104
#define IDC_WRITEBTN 201

static const wchar_t *ABOUT_TEXT = L"CalibWin32 v1 - calibration target. Menus: File, Help.";
static const char *PROBE_NAME = "calib_win32_probe.txt";
static const char *PROBE_BODY = "calib-win32 says hello";

static void write_probe(void) {
    wchar_t tmp[MAX_PATH];
    GetTempPathW(MAX_PATH, tmp);
    wchar_t path[MAX_PATH];
    _snwprintf(path, MAX_PATH, L"%s\\calib_win32_probe.txt", tmp);
    FILE *f = _wfopen(path, L"w");
    if (f) {
        fputs(PROBE_BODY, f);
        fclose(f);
    }
}

static LRESULT CALLBACK WndProc(HWND h, UINT m, WPARAM w, LPARAM l) {
    switch (m) {
    case WM_COMMAND:
        switch (LOWORD(w)) {
        case IDM_OPEN:
            MessageBoxW(h, L"Open pressed (no-op in calib build).", L"CalibWin32", MB_OK);
            break;
        case IDM_SAVE:
            MessageBoxW(h, L"Save pressed (no-op in calib build).", L"CalibWin32", MB_OK);
            break;
        case IDM_EXIT:
            PostQuitMessage(0);
            break;
        case IDM_ABOUT:
            MessageBoxW(h, ABOUT_TEXT, L"About CalibWin32", MB_OK);
            break;
        case IDC_WRITEBTN:
            write_probe();
            MessageBoxW(h, L"Probe file written to %TEMP%.", L"CalibWin32", MB_OK);
            break;
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    }
    return DefWindowProcW(h, m, w, l);
}

int WINAPI wWinMain(HINSTANCE hi, HINSTANCE hp, PWSTR cmd, int show) {
    (void)hp;
    (void)cmd;
    WNDCLASSW wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hi;
    wc.lpszClassName = L"CalibWin32";
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassW(&wc);

    HMENU bar = CreateMenu();
    HMENU file = CreatePopupMenu();
    AppendMenuW(file, MF_STRING, IDM_OPEN, L"&Open");
    AppendMenuW(file, MF_STRING, IDM_SAVE, L"&Save");
    AppendMenuW(file, MF_SEPARATOR, 0, NULL);
    AppendMenuW(file, MF_STRING, IDM_EXIT, L"E&xit");
    HMENU help = CreatePopupMenu();
    AppendMenuW(help, MF_STRING, IDM_ABOUT, L"&About CalibWin32");
    AppendMenuW(bar, MF_POPUP, (UINT_PTR)file, L"&File");
    AppendMenuW(bar, MF_POPUP, (UINT_PTR)help, L"&Help");

    HWND win = CreateWindowW(L"CalibWin32", L"CalibWin32 - calibration target",
                             WS_OVERLAPPEDWINDOW, 200, 200, 480, 320,
                             NULL, bar, hi, NULL);
    CreateWindowW(L"BUTTON", L"Write file", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                  24, 24, 140, 36, win, (HMENU)(INT_PTR)IDC_WRITEBTN, hi, NULL);
    ShowWindow(win, show);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return 0;
}
