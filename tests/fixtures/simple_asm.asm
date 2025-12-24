; Simple assembly program for testing reverse engineering
; This is x86 assembly that can be assembled with NASM

section .data
    hello db 'Hello from assembly!', 0xA, 0
    result_msg db 'Result: %d', 0xA, 0

section .text
    global _start

_start:
    ; Print hello message
    mov eax, 4          ; sys_write
    mov ebx, 1          ; stdout
    mov ecx, hello      ; message
    mov edx, 20         ; length
    int 0x80            ; syscall

    ; Simple calculation: 5 + 3 = 8
    mov eax, 5
    add eax, 3          ; eax = 8

    ; Print result (simplified - would need more code for full printf)
    ; For testing purposes, we just exit with the result

    ; Exit
    mov eax, 1          ; sys_exit
    mov ebx, 0          ; exit code
    int 0x80            ; syscall
