import sys

import yaramod


class BoolSimplifier(yaramod.ModifyingVisitor):
    def visit_AndExpression(self, expr):
        left_expr = expr.left_operand.accept(self)
        right_expr = expr.right_operand.accept(self)

        left_bool = left_expr.expression if (left_expr and isinstance(left_expr.expression, yaramod.BoolLiteralExpression)) else None
        right_bool = right_expr.expression if (right_expr and isinstance(right_expr.expression, yaramod.BoolLiteralExpression)) else None

        # If both sides of AND are boolean constants then determine the value based on truth table of AND
        # T and T = T
        # T and F = F
        # F and T = F
        # F and F = F
        if left_bool and right_bool:
            return yaramod.bool_val(left_bool.value and right_bool.value).get()
        # Only left-hand side is boolean constant
        elif left_bool:
            # F and X = F
            # T and X = X
            return yaramod.bool_val(False).get() if not left_bool.value else expr.right_operand
        # Only right-hand side is boolean constant
        elif right_bool:
            # X and F = F
            # X and T = X
            return yaramod.bool_val(False).get() if not right_bool.value else expr.left_operand

        return self.default_handler(expr, left_expr, right_expr)

    def visit_OrExpression(self, expr):
        left_expr = expr.left_operand.accept(self)
        right_expr = expr.right_operand.accept(self)

        left_bool = left_expr.expression if (left_expr and isinstance(left_expr.expression, yaramod.BoolLiteralExpression)) else None
        right_bool = right_expr.expression if (right_expr and isinstance(right_expr.expression, yaramod.BoolLiteralExpression)) else None

        # If both sides of OR are boolean constants then determine the value based on truth table of OR
        # T or T = T
        # T or F = T
        # F or T = T
        # F or F = F
        if left_bool and right_bool:
            return yaramod.bool_val(left_bool.value or right_bool.value).get()
        # Only left-hand side is boolean constant
        elif left_bool:
            # T or X = T
            # F or X = X
            return yaramod.bool_val(True).get() if left_bool.value else expr.right_operand
        # Only right-hand side is boolean constant
        elif right_bool:
            # X or T = T
            # X or F = X
            return yaramod.bool_val(True).get() if right_bool.value else expr.left_operand

        return self.default_handler(expr, left_expr, right_expr)

    def visit_NotExpression(self, expr):
        new_expr = expr.operand.accept(self)

        # Negate the value of boolean constant
        bool_val = new_expr.expression if (new_expr and isinstance(new_expr.expression, yaramod.BoolLiteralExpression)) else None
        if bool_val:
            return yaramod.bool_val(not bool_val.value).get()

        return self.default_handler(expr, new_expr)

    def visit_ParenthesesExpression(self, expr):
        new_expr = expr.enclosed_expr.accept(self)

        # Remove parentheses around boolean constants and lift their value up
        bool_val = new_expr.expression if (new_expr and isinstance(new_expr.expression, yaramod.BoolLiteralExpression)) else None
        if bool_val:
            return yaramod.bool_val(bool_val.value).get()

        return self.default_handler(expr, new_expr)

    def visit_BoolLiteralExpression(self, expr):
        # Lift up boolean value
        return yaramod.bool_val(expr.value).get()


def main():
    if len(sys.argv) != 2:
        print('Usage: dump_rules_ast.py YARA_FILE')
        sys.exit(1)

    simplifier = BoolSimplifier()

    yara_file = yaramod.parse_file(sys.argv[1])
    for rule in yara_file.rules:
        print('==== RULE: {}'.format(rule.name))
        print('==== BEFORE')
        print(rule.text)
        simplifier.modify(rule.condition)
        print('==== AFTER')
        print(rule.text)


if __name__ == '__main__':
    main()
