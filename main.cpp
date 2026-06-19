#include <windows.h>
#include "RunDialog.h"

const wchar_t CLASS_NAME[] = L"CelineWin7Shell";

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_CREATE:
        CreateWindowW(L"BUTTON", L"Run...", WS_VISIBLE | WS_CHILD,
                      20, 20, 100, 30, hwnd, (HMENU)1001, nullptr, nullptr);
        CreateWindowW(L"STATIC", L"Celine Shell - Win32 Prototype", WS_VISIBLE | WS_CHILD,
                      20, 70, 380, 24, hwnd, nullptr, nullptr, nullptr);
        break;
    case WM_COMMAND:
        if (LOWORD(wParam) == 1001) {
            ShowRunDialog(hwnd);
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE, PWSTR, int nCmdShow) {
    WNDCLASS wc = {};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(0, CLASS_NAME, L"Celine Win32 Shell Prototype",
                               WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 560, 420,
                               nullptr, nullptr, hInstance, nullptr);

    if (!hwnd) {
        return 0;
    }

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg = {};
    while (GetMessage(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return (int)msg.wParam;
}
