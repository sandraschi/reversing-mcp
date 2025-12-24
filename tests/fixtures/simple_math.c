#include <stdio.h>

int add_numbers(int a, int b) {
    return a + b;
}

int multiply_numbers(int a, int b) {
    return a * b;
}

int main() {
    int x = 10;
    int y = 20;
    int sum = add_numbers(x, y);
    int product = multiply_numbers(x, y);

    printf("Sum: %d\n", sum);
    printf("Product: %d\n", product);
    return 0;
}
