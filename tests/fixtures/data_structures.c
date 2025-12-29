#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char name[50];
    int age;
    float salary;
} Employee;

Employee* create_employee(const char* name, int age, float salary) {
    Employee* emp = (Employee*)malloc(sizeof(Employee));
    strcpy(emp->name, name);
    emp->age = age;
    emp->salary = salary;
    return emp;
}

void print_employee(Employee* emp) {
    printf("Name: %s\n", emp->name);
    printf("Age: %d\n", emp->age);
    printf("Salary: %.2f\n", emp->salary);
}

int calculate_bonus(Employee* emp) {
    if (emp->age > 30) {
        return (int)(emp->salary * 0.1);
    }
    return 0;
}

int main() {
    Employee* employees[3];

    employees[0] = create_employee("Alice", 25, 50000.0);
    employees[1] = create_employee("Bob", 35, 60000.0);
    employees[2] = create_employee("Charlie", 28, 55000.0);

    for (int i = 0; i < 3; i++) {
        printf("Employee %d:\n", i + 1);
        print_employee(employees[i]);
        int bonus = calculate_bonus(employees[i]);
        printf("Bonus: %d\n\n", bonus);
        free(employees[i]);
    }

    return 0;
}





