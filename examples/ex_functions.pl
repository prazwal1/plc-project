# Function abstraction with value parameter passing.
# Changing a parameter inside the function does NOT affect the caller.

def int factorial(int n) {
    if n = 0 then {
        return 1;
    } else {
        return n * factorial(n - 1);
    };
}

def float to_fahrenheit(float c) {
    return c *. 1.8 +. 32.0;
}

n      = 6;
result = factorial(n);
print(n);       # still 6 -- value passing, n unchanged
print(result);  # 720

temp = to_fahrenheit(100.0);
print(temp);    # 212.0
