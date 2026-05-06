# ================================================================
# examples.pl  --  one program demonstrating every feature in the
#                  assignment spec, in the order the spec lists them.
# ================================================================


# ----------------------------------------------------------------
# 1. TYPES  (int, float, bool, string)
#    No explicit declaration -- type is inferred from first use.
# ----------------------------------------------------------------

age    = 25;
height = 1.75;
flag   = true;
name   = "Alice";

print(age);
print(height);
print(flag);
print(name);


# ----------------------------------------------------------------
# 2. ARITHMETIC OPERATORS AND PRECEDENCE
#    Separate operators for int (+  -  *  /) and float (+. -. *. /.)
#    Multiplication / division bind tighter than addition / subtraction.
# ----------------------------------------------------------------

# Integer arithmetic  (2 + 3 * 4  =>  14, not 20)
a = 2 + 3 * 4;
print(a);

# Float arithmetic
pi    = 3.14159;
r     = 5.0;
circ  = 2.0 *. pi *. r;
print(circ);

# String concatenation with  ^
greeting = "Hello, " ^ name ^ "!";
print(greeting);


# ----------------------------------------------------------------
# 3. BOOLEAN EXPRESSIONS  (=  and  <>)
#    Both sides must be the same arithmetic type; result is bool.
# ----------------------------------------------------------------

eq_test  = 10 = 10;
neq_test = 3 <> 7;
print(eq_test);
print(neq_test);


# ----------------------------------------------------------------
# 4. ASSIGNMENT STATEMENT
#    The right-hand side can be any expression; the variable keeps
#    the inferred type for the rest of the program.
# ----------------------------------------------------------------

x = 100;
x = x - 1;
print(x);


# ----------------------------------------------------------------
# 5. IF-THEN-ELSE
# ----------------------------------------------------------------

score = 75;
if score <> 100 then {
    print(score);
} else {
    print(100);
};


# ----------------------------------------------------------------
# 6. WHILE LOOP
# ----------------------------------------------------------------

i   = 1;
sum = 0;
while i <> 6 do {
    sum = sum + i;
    i   = i + 1;
};
print(sum);


# ----------------------------------------------------------------
# 7. FUNCTIONS  (value parameter passing)
#    Parameters are copies -- mutating them inside the function
#    does not affect the caller.
# ----------------------------------------------------------------

def int factorial(int n) {
    if n = 0 then {
        return 1;
    } else {
        return n * factorial(n - 1);
    };
}

def float celsius_to_fahrenheit(float c) {
    return c *. 1.8 +. 32.0;
}

def string repeat(string s, int times) {
    result = "";
    i = 0;
    while i <> times do {
        result = result ^ s;
        i = i + 1;
    };
    return result;
}

# Value-passing demo: n inside factorial is a copy.
n  = 6;
f  = factorial(n);
print(f);

temp_c = 100.0;
temp_f = celsius_to_fahrenheit(temp_c);
print(temp_f);

echoed = repeat("ha", 3);
print(echoed);


# ----------------------------------------------------------------
# 8. PRINT  (works with any type)
# ----------------------------------------------------------------

print(42);
print(3.14);
print(true);
print("done");
