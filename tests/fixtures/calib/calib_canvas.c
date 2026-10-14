/* calib_canvas.c - hermetic calibration target #2 (canvas-analog, B3 path).
 *
 * A single window with NO menu and NO child controls: everything is painted
 * in WM_PAINT (title text + two fake buttons) and hit-tested in
 * WM_LBUTTONDOWN. UIA sees one empty canvas window - exactly the shape that
 * forces the B3 OCR/coordinate fallback (Delphi/Directmedia analog).
 * Known answers: painted strings, click rects, files written.
 * Expected manifest: tests/fixtures/calib/expected.json (CALIB_CANVAS).
 * Build: scripts/build_calib.py (MSVC cl.exe) or just calib.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>

typedef struct {
    RECT rc;
    const wchar_t *label;
    const char *probe;
    const char *body;
} FakeBtn;

static FakeBtn BTNS[] = {
    {{40, 90, 220, 130}, L"Save Report", "calib_canvas_report.txt", "calib-canvas report"},
    {{40, 150, 220, 190}, L"Export Data", "calib_canvas_export.txt", "calib-canvas export"},
};
static const wchar_t *TITLE_TEXT = L"CalibCanvas - painted UI calibration";

static void write_probe(const char *name, const char *body) {
    char tmp[MAX_PATH];
    GetTempPathA(MAX_PATH, tmp);
    char path[MAX_PATH];
    _snprintf(path, MAX_PATH, "%s\\%s", tmp, name);
    FILE *f = fopen(path, "w");
    if (f) {
        fputs(body, f);
        fclose(f);
    }
}

static LRESULT CALLBACK WndProc(HWND h, UINT m, WPARAM w, LPARAM l) {
    switch (m) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC dc = BeginPaint(h, &ps);
        TextOutW(dc, 40, 30, TITLE_TEXT, (int)wcslen(TITLE_TEXT));
        for (int i = 0; i < 2; i++) {
            Rectangle(dc, BTNS[i].rc.left, BTNS[i].rc.top, BTNS[i].rc.right, BTNS[i].rc.bottom);
            TextOutW(dc, BTNS[i].rc.left + 12, BTNS[i].rc.top + 12,
                     BTNS[i].label, (int)wcslen(BTNS[i].label));
        }
        EndPaint(h, &ps);
        break;
    }
    case WM_LBUTTONDOWN: {
        int x = (int)(short)LOWORD(l), y = (int)(short)HIWORD(l);
        for (int i = 0; i < 2; i++) {
            if (x >= BTNS[i].rc.left && x <= BTNS[i].rc.right &&
                y >= BTNS[i].rc.top && y <= BTNS[i].rc.bottom) {
                write_probe(BTNS[i].probe, BTNS[i].body);
                InvalidateRect(h, NULL, TRUE);
            }
        }
        break;
    }
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
    wc.lpszClassName = L"CalibCanvas";
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassW(&wc);
    HWND win = CreateWindowW(L"CalibCanvas", L"CalibCanvas",
                             WS_OVERLAPPEDWINDOW, 200, 200, 480, 320,
                             NULL, NULL, hi, NULL);
    ShowWindow(win, show);
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return 0;
}
