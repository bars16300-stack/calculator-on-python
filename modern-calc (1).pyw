import customtkinter as ctk
import tkinter as tk
import math
import re

# ============================================================
#  ЧАСТЬ 1: ПАРСЕР ВЫРАЖЕНИЙ (БЕЗ EVAL)
# ============================================================
TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<NUMBER>\d+\.\d*|\.\d+|\d+)
      | (?P<NAME>[a-zA-Z_][a-zA-Z_0-9]*)
      | (?P<OP>\*\*|[-+*/%(),^])
    )
""", re.VERBOSE)

class Token:
    def __init__(self, kind, value, pos):
        self.kind, self.value, self.pos = kind, value, pos
    def __repr__(self):
        return f"{self.kind}({self.value})"

def tokenize(text):
    tokens, pos = [], 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise SyntaxError(f"Непонятный символ: {text[pos]!r}")
        kind = m.lastgroup
        tokens.append(Token(kind, m.group(kind), pos))
        pos = m.end()
    tokens.append(Token("EOF", "", pos))
    return tokens

class Node:
    def eval(self, env): ...

class Number(Node):
    def __init__(self, value): self.value = value
    def eval(self, env): return self.value

class Variable(Node):
    def __init__(self, name): self.name = name
    def eval(self, env):
        if self.name not in env:
            raise NameError(f"Неизвестное имя: {self.name}")
        return env[self.name]

class UnaryOp(Node):
    def __init__(self, op, operand): self.op, self.operand = op, operand
    def eval(self, env):
        v = self.operand.eval(env)
        return -v if self.op == "-" else +v

class BinOp(Node):
    def __init__(self, op, left, right): self.op, self.left, self.right = op, left, right
    def eval(self, env):
        a = self.left.eval(env)
        b = self.right.eval(env)
        if self.op == "+": return a + b
        if self.op == "-": return a - b
        if self.op == "*": return a * b
        if self.op == "/":
            if b == 0: raise ZeroDivisionError("Деление на ноль")
            return a / b
        if self.op == "%":
            if b == 0: raise ZeroDivisionError("Остаток от деления на ноль")
            return a % b
        if self.op == "**": return a ** b
        raise ValueError(f"Неизвестный оператор {self.op}")

class FuncCall(Node):
    FUNCS = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "log": math.log, "log10": math.log10, "log2": math.log2,
        "exp": math.exp, "abs": abs, "round": round,
        "floor": math.floor, "ceil": math.ceil,
    }
    def __init__(self, name, args): self.name, self.args = name, args
    def eval(self, env):
        if self.name not in self.FUNCS:
            raise NameError(f"Неизвестная функция: {self.name}")
        vals = [a.eval(env) for a in self.args]
        return self.FUNCS[self.name](*vals)

CONSTANTS = {"pi": math.pi, "e": math.e}

class Parser:
    def __init__(self, tokens):
        self.tokens, self.i = tokens, 0

    def peek(self): return self.tokens[self.i]
    def advance(self): tok = self.tokens[self.i]; self.i += 1; return tok
    
    def match(self, kind, value=None):
        tok = self.peek()
        if tok.kind == kind and (value is None or tok.value == value):
            return self.advance()
        return None
        
    def expect(self, kind, value=None):
        tok = self.match(kind, value)
        if tok is None:
            got = self.peek()
            want = value if value else kind
            raise SyntaxError(f"Ожидалось {want!r}, а встретилось {got.value!r}")
        return tok

    def parse_expr(self):
        node = self.parse_term()
        while True:
            tok = self.match("OP", "+") or self.match("OP", "-")
            if not tok: break
            node = BinOp(tok.value, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_power()
        while True:
            tok = self.match("OP", "*") or self.match("OP", "/") or self.match("OP", "%")
            if not tok: break
            node = BinOp(tok.value, node, self.parse_power())
        return node

    def parse_power(self):
        node = self.parse_unary()
        if self.match("OP", "**") or self.match("OP", "^"):
            return BinOp("**", node, self.parse_power())
        return node

    def parse_unary(self):
        tok = self.match("OP", "+") or self.match("OP", "-")
        if tok: return UnaryOp(tok.value, self.parse_unary())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.advance()
            return Number(float(tok.value))
        if tok.kind == "NAME":
            self.advance()
            name = tok.value
            if self.match("OP", "("):
                args = []
                if not self.match("OP", ")"):
                    args.append(self.parse_expr())
                    while self.match("OP", ","):
                        args.append(self.parse_expr())
                    self.expect("OP", ")")
                return FuncCall(name, args)
            return Variable(name)
        if self.match("OP", "("):
            node = self.parse_expr()
            self.expect("OP", ")")
            return node
        raise SyntaxError(f"Неожиданный токен {tok.value!r}")

def evaluate(text):
    tokens = tokenize(text)
    parser = Parser(tokens)
    tree = parser.parse_expr()
    if parser.peek().kind != "EOF":
        raise SyntaxError(f"Лишний токен {parser.peek().value!r}")
    return tree.eval(CONSTANTS), tree


# ============================================================
#  ЧАСТЬ 2: СОВРЕМЕННЫЙ ИНТЕРФЕЙС (CustomTkinter)
# ============================================================
BG        = "#0b0713"
PANEL     = "#151022"
BTN       = "#1e1630"
BTN_HOVER = "#2b1f47"
ACCENT    = "#a855f7"
ACCENT_2  = "#7c3aed"
TEXT      = "#f3e8ff"
MUTED     = "#8b7ba8"
DANGER    = "#f472b6"

ctk.set_appearance_mode("dark")

class NeonCalculator(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG)
        self.title("Neon Calc")
        self.geometry("460x640")
        self.minsize(420, 600)
        self.configure(fg_color=BG)

        self._pulse_job = None
        self._result_anim_job = None
        self._glow_phase = 0.0

        self._build_ui()
        self.bind("<Return>", lambda e: self.calculate())
        self.bind("<KP_Enter>", lambda e: self.calculate())
        self.bind("<Escape>", lambda e: self.clear())
        self.after(60, self._animate_glow)

    def _build_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="NEON CALC", font=("Consolas", 26, "bold"), text_color=ACCENT
        )
        self.title_label.pack(pady=(18, 4))

        ctk.CTkLabel(
            self, text="parser · no eval · pure math", font=("Consolas", 11), text_color=MUTED
        ).pack(pady=(0, 12))

        self.expr_var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self, textvariable=self.expr_var,
            font=("Consolas", 20), height=56, corner_radius=14,
            fg_color=PANEL, border_color=ACCENT_2, border_width=2,
            text_color=TEXT, placeholder_text="2 + 3 * sqrt(16)",
            placeholder_text_color=MUTED,
        )
        self.entry.pack(fill="x", padx=18, pady=(0, 10))
        self.entry.focus_set()

        self.result_label = ctk.CTkLabel(
            self, text="0", font=("Consolas", 34, "bold"), text_color=TEXT, anchor="e"
        )
        self.result_label.pack(fill="x", padx=22, pady=(0, 14))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        for c in range(5):
            grid.columnconfigure(c, weight=1, uniform="col")
        for r in range(5):
            grid.rowconfigure(r, weight=1, uniform="row")

        layout = [
            ["C", "(", ")", "/", "⌫"],
            ["7", "8", "9", "*", "%"],
            ["4", "5", "6", "-", "sqrt("],
            ["1", "2", "3", "+", "**"],
            ["0", ".", "pi", "e", "="],
        ]

        for r, row in enumerate(layout):
            for c, label in enumerate(row):
                kind = "op"
                if label in "0123456789.": kind = "num"
                elif label == "=": kind = "eq"
                elif label in ("C", "⌫"): kind = "danger"
                
                btn = self._make_button(grid, label, kind)
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        self.history_frame = ctk.CTkScrollableFrame(
            self, height=110, fg_color=PANEL, corner_radius=14
        )
        self.history_frame.pack(fill="x", padx=18, pady=(0, 16))
        self.history_items = []

    def _make_button(self, parent, label, kind):
        styles = {
            "num":    dict(fg_color=BTN,       hover_color=BTN_HOVER, text_color=TEXT),
            "op":     dict(fg_color=ACCENT_2,  hover_color=ACCENT,    text_color="#fff"),
            "eq":     dict(fg_color=ACCENT,    hover_color="#c084fc", text_color="#14061f"),
            "danger": dict(fg_color="#3a1030", hover_color=DANGER,    text_color=DANGER),
        }[kind]
        
        btn = ctk.CTkButton(
            parent, text=label, font=("Consolas", 18, "bold"),
            corner_radius=14, height=52, **styles
        )
        btn.configure(command=lambda l=label, b=btn: self._on_click(l, b))
        btn.bind("<Enter>", lambda e, b=btn: b.configure(border_width=1, border_color=ACCENT))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(border_width=0))
        return btn

    def _animate_glow(self):
        self._glow_phase += 0.08
        t = (math.sin(self._glow_phase) + 1) / 2
        color = self._lerp_color("#7c3aed", "#e9d5ff", t)
        self.title_label.configure(text_color=color)
        self.after(60, self._animate_glow)

    def _pulse(self, widget):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
        orig = widget.cget("fg_color")
        widget.configure(fg_color="#c084fc")
        self._pulse_job = self.after(110, lambda: widget.configure(fg_color=orig))

    def _animate_result(self, text):
        if self._result_anim_job:
            self.after_cancel(self._result_anim_job)
        sizes = [34, 38, 42, 40, 38, 36, 34]
        colors = ["#a855f7", "#c084fc", "#e9d5ff", "#ffffff", "#e9d5ff", "#c084fc", "#a855f7"]

        def step(i=0):
            if i >= len(sizes):
                self.result_label.configure(font=("Consolas", 34, "bold"), text_color=TEXT)
                return
            self.result_label.configure(
                text=text, font=("Consolas", sizes[i], "bold"), text_color=colors[i]
            )
            self._result_anim_job = self.after(35, lambda: step(i + 1))
        step()

    @staticmethod
    def _lerp_color(c1, c2, t):
        def h(c): return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
        a, b = h(c1), h(c2)
        return "#{:02x}{:02x}{:02x}".format(*(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))

    def _on_click(self, label, btn):
        self._pulse(btn)
        self.on_button(label)

    def on_button(self, label):
        if label == "=": self.calculate()
        elif label == "C": self.clear()
        elif label == "⌫": self.expr_var.set(self.expr_var.get()[:-1])
        else: self.expr_var.set(self.expr_var.get() + label)

    def clear(self):
        self.expr_var.set("")
        self._animate_result("0")

    def calculate(self):
        expr = self.expr_var.get().strip()
        if not expr: return
        try:
            result, _ = evaluate(expr)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self._animate_result(str(result))
            self._add_history(expr, result)
        except ZeroDivisionError as e:
            self._animate_result("÷0")
            self._add_history(expr, f"⚠ {e}", error=True)
        except SyntaxError as e:
            self._animate_result("syntax")
            self._add_history(expr, f"⚠ {e}", error=True)
        except NameError as e:
            self._animate_result("name?")
            self._add_history(expr, f"⚠ {e}", error=True)
        except Exception as e:
            self._animate_result("error")
            self._add_history(expr, f"⚠ {e}", error=True)

    def _add_history(self, expr, result, error=False):
        text = f"{expr}  =  {result}"
        color = DANGER if error else MUTED
        row = ctk.CTkLabel(
            self.history_frame, text=text, anchor="w",
            font=("Consolas", 12), text_color=color
        )
        row.pack(fill="x", padx=8, pady=2)
        self.history_items.append(row)
        if len(self.history_items) > 30:
            old = self.history_items.pop(0)
            old.destroy()

if __name__ == "__main__":
    app = NeonCalculator()
    app.mainloop()