#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <direct.h>
#define mkdir _mkdir
#else
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
#endif

// Suspicious file operations
int create_hidden_files() {
    printf("Creating hidden system files...\n");

#ifdef _WIN32
    // Create hidden file
    HANDLE hFile = CreateFile("C:\\Windows\\System32\\suspicious.dll",
                             GENERIC_WRITE, 0, NULL, CREATE_ALWAYS,
                             FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM, NULL);

    if (hFile != INVALID_HANDLE_VALUE) {
        const char* content = "MZ...suspicious DLL content...";
        DWORD written;
        WriteFile(hFile, content, strlen(content), &written, NULL);
        CloseHandle(hFile);
        printf("Created hidden system file\n");
    }

    // Try to access system directories
    if (CreateDirectory("C:\\Windows\\System32\\evil", NULL)) {
        printf("Created directory in System32\n");
    }

#else
    // Unix-like systems
    FILE* f = fopen("/etc/suspicious.conf", "w");
    if (f) {
        fprintf(f, "malicious=config\n");
        fclose(f);
        printf("Created file in /etc/\n");
    }

    mkdir("/tmp/evil_directory", 0755);
    printf("Created directory in /tmp/\n");
#endif

    return 0;
}

// Registry manipulation (Windows-specific suspicious behavior)
int manipulate_registry() {
#ifdef _WIN32
    HKEY hKey;
    printf("Attempting registry manipulation...\n");

    // Try to open registry keys
    if (RegOpenKeyEx(HKEY_LOCAL_MACHINE,
                    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                    0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        const char* evil_path = "C:\\evil.exe";
        RegSetValueEx(hKey, "EvilService", 0, REG_SZ,
                     (BYTE*)evil_path, strlen(evil_path) + 1);
        RegCloseKey(hKey);
        printf("Modified registry autorun\n");
    }
#endif
    return 0;
}

// Process manipulation
int inject_into_process() {
    printf("Attempting process injection...\n");

#ifdef _WIN32
    // Get current process
    HANDLE hProcess = GetCurrentProcess();

    // Allocate memory (suspicious)
    LPVOID addr = VirtualAllocEx(hProcess, NULL, 1024,
                                MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

    if (addr) {
        const char* shellcode = "\x90\x90\x90..."; // NOP sled
        WriteProcessMemory(hProcess, addr, shellcode, strlen(shellcode), NULL);
        printf("Injected shellcode into process memory\n");
    }
#endif

    return 0;
}

int main() {
    printf("Suspicious File System Activity Program\n");
    printf("======================================\n");

    create_hidden_files();
    manipulate_registry();
    inject_into_process();

    printf("Program completed. Performed suspicious file system operations.\n");
    return 0;
}





