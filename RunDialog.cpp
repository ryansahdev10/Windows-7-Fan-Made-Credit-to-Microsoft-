#include "RunDialog.h"
#include <windows.h>

LRESULT CALLBACK RunDlgProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK) {
            wchar_t command[256];
            GetDlgItemText(hwnd, 1002, command, 256);
            MessageBox(hwnd, command, L"Execute", MB_OK | MB_ICONINFORMATION);
            EndDialog(hwnd, IDOK);
        } else if (LOWORD(wParam) == IDCANCEL) {
            EndDialog(hwnd, IDCANCEL);
        }
        break;
    }
    return FALSE;
}

void ShowRunDialog(HWND owner) {
    const wchar_t CLASSNAME[] = L"CelineRunDialog";
    DialogBoxParam(GetModuleHandle(nullptr), MAKEINTRESOURCE(101), owner, RunDlgProc, 0);
}
