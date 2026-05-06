# Arithmetic operators.
# Int:   +  -  *  /      Float: +.  -.  *.  /.      String: ^
# Precedence: * / before + -  (same for float counterparts)

# Integer -- 2 + 3*4 = 14, not 20
a = 2 + 3 * 4;
print(a);

# Float
area = 3.14159 *. 5.0 *. 5.0;
print(area);

# String concatenation
msg = "hello" ^ ", " ^ "world";
print(msg);
