#include <stdio.h>

void printEvenAfter() {
    int n;
    scanf("%d", &n);

    // Base case
    if (n < 0)
        return;

    // Recursive call first
    printEvenAfter();

    // Print while returning
    if (n % 2 == 0)
        printf("%d ", n);
}

int main() {
    printEvenAfter();
    return 0;
}