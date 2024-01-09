import spaces_around_assignment_linter_v0 as spaces_linter_v0
import spaces_around_assignment_linter_v1 as spaces_linter_v1

print("Spaces Linter V0:")
print(spaces_linter_v0.lint_spaces_around_assignment_v0("a = 10"))
print(spaces_linter_v0.lint_spaces_around_assignment_v0("a =10"))
print(spaces_linter_v0.lint_spaces_around_assignment_v0("a= 10"))
print(spaces_linter_v0.lint_spaces_around_assignment_v0("a=10"))
print(spaces_linter_v0.lint_spaces_around_assignment_v0("a == 10 \n b = c \n c=d"))

print("Spaces Linter V1:")
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a = 10"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a =10"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a= 10"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a=10"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a == 10 \n b = c \n c=d"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a == 10 \n b = c"))
print(spaces_linter_v1.lint_spaces_around_assignment_v1("a *= 10 \n b = c"))

