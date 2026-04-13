import math
import re
import sympy as sp
import mpmath

# Globale Speicherung für benutzerdefinierte Funktionen
USER_DEFINITIONS = {}

def evaluiere(ausdruck: str, decimals: int = 10, angle_mode: str = 'deg'):
    global USER_DEFINITIONS
    
    ausdruck = ausdruck.strip()
    
    # -----------------------------
    # Hilfsfunktion: Formatierung des Ergebnisses
    # -----------------------------
    def format_result(obj):
        # Rekursiv für Vektoren
        if isinstance(obj, Vector):
            elements = [format_result(x) for x in obj.data]
            return "[" + "; ".join(elements) + "]"
            
        # Zahlen (Float/Int)
        if isinstance(obj, (int, float, sp.Float, sp.Integer, mpmath.mpf)):
            try:
                val = float(obj)
                if abs(val) < 10**(-decimals-2): val = 0.0
                else: val = round(val, decimals)
                
                if val.is_integer(): val = int(val)
                return str(val).replace('.', ',')
            except:
                return str(obj).replace('.', ',')

        # Strings (algebraische Ausdrücke, Fehlermeldungen etc.)
        text = str(obj)
        
        # 1. Komma statt Punkt
        text = text.replace('.', ',')
        
        # 2. Potenzen
        text = text.replace('**', '^')
        
        # 3. Implizite Multiplikation verschönern (z.B. 4*x -> 4x)
        # Entfernt * zwischen Zahl und Buchstabe/Klammer
        text = re.sub(r'(\d)\*([a-zA-Z(])', r'\1\2', text)
        
        # 4. Leerzeichen-Regeln anwenden
        text = text.replace(' + ', ' +')
        text = text.replace(' - ', ' -')
        text = text.replace(' = ', ' =')
        
        return text

    # -----------------------------
    # 0. Befehls-Verarbeitung
    # -----------------------------
    
    def apply_implicit_multiplication(text):
        text = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', text)
        text = re.sub(r'(\))([a-zA-Z(])', r'\1*\2', text)
        return text

    if ausdruck.startswith("def "):
        try:
            match = re.match(r"^def\s+([a-zA-Z][a-zA-Z0-9]*)\(([a-zA-Z][a-zA-Z0-9]*)\)\s*:\s*(.+)$", ausdruck)
            if match:
                name, var, body = match.groups()
                body = body.replace(',', '.')
                body = apply_implicit_multiplication(body)
                body = body.replace('^', '**')

                forbidden = ['sqrt', 'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'nsolve', 'lsolve', 
                             'root', 'e', 'pi', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
                             'binco', 'binom', 'cbinom']
                if name in forbidden:
                    return f"Fehler: Der Name '{name}' ist reserviert."
                    
                USER_DEFINITIONS[name] = {'var': var, 'body': body}
                return "Funktion erfolgreich definiert"
            else:
                return "Format-Fehler. Verwende: def f(x): Ausdruck"
        except Exception as e:
            return f"Fehler bei Definition: {str(e)}"

    if ausdruck.startswith("deldef"):
        rest = ausdruck[6:].strip()
        if not rest:
            USER_DEFINITIONS.clear()
            return "Alle Definitionen gelöscht."
        else:
            match = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)(\(.*\))?$", rest)
            if match:
                name = match.group(1)
                if name in USER_DEFINITIONS:
                    del USER_DEFINITIONS[name]
                    return f"Funktion '{name}' gelöscht."
                else:
                    return f"Funktion '{name}' nicht gefunden."
            return "Fehler: Name nicht erkannt."

    if ausdruck == "showdef":
        if not USER_DEFINITIONS:
            return "Keine Funktionen definiert."
        lines = []
        for name, data in USER_DEFINITIONS.items():
            pretty_body = data['body'].replace('**', '^')
            lines.append(f"{name}({data['var']}) = {pretty_body}")
        return "\n".join(lines)

    # -----------------------------
    # 1. Vorverarbeitung
    # -----------------------------
    
    ausdruck = ausdruck.replace(',', '.')

    def replace_factorials(text):
        result = text
        while True:
            bang_idx = None
            for idx, char in enumerate(result):
                if char == '!' and (idx + 1 >= len(result) or result[idx + 1] != '='):
                    bang_idx = idx
                    break

            if bang_idx is None:
                return result

            left = bang_idx - 1
            while left >= 0 and result[left].isspace():
                left -= 1

            if left < 0:
                raise ValueError("Fehlerhafte Fakultätssyntax.")

            if result[left] in ')]':
                opener = '(' if result[left] == ')' else '['
                closer = result[left]
                depth = 1
                start = left - 1
                while start >= 0 and depth > 0:
                    if result[start] == closer:
                        depth += 1
                    elif result[start] == opener:
                        depth -= 1
                    start -= 1
                if depth != 0:
                    raise ValueError("Fehlende Klammer vor Fakultät.")
                operand_start = start + 1
            else:
                start = left
                while start >= 0 and (result[start].isalnum() or result[start] in '._'):
                    start -= 1
                operand_start = start + 1

            operand = result[operand_start:bang_idx].strip()
            if not operand:
                raise ValueError("Fehlerhafte Fakultätssyntax.")

            result = result[:operand_start] + f"factorial_strict({operand})" + result[bang_idx + 1:]

    def extract_balanced_call(text, func_name):
        start_idx = text.find(func_name + "(")
        if start_idx == -1: return None, None, None
        
        open_parens = 1
        curr_idx = start_idx + len(func_name) + 1
        while open_parens > 0 and curr_idx < len(text):
            if text[curr_idx] == '(': open_parens += 1
            elif text[curr_idx] == ')': open_parens -= 1
            curr_idx += 1
            
        if open_parens == 0:
            full_match = text[start_idx:curr_idx]
            content = text[start_idx + len(func_name) + 1 : curr_idx - 1]
            return full_match, content, start_idx
        return None, None, None

    # -----------------------------
    # 1.5 Expansion benutzerdefinierter Funktionen
    # -----------------------------
    try:
        expansion_loops = 0
        while expansion_loops < 20:
            replaced_something = False
            for name in sorted(USER_DEFINITIONS.keys(), key=len, reverse=True):
                data = USER_DEFINITIONS[name]
                match_str, content, _ = extract_balanced_call(ausdruck, name)
                if match_str:
                    var_name = data['var']
                    body = data['body']
                    arg_subbed = f"({content})"
                    pattern = r'(?<![a-zA-Z0-9_])' + re.escape(var_name) + r'(?![a-zA-Z0-9_])'
                    expanded_body = re.sub(pattern, lambda _: arg_subbed, body)
                    ausdruck = ausdruck.replace(match_str, f"({expanded_body})")
                    replaced_something = True
            if not replaced_something: break
            expansion_loops += 1
    except Exception as e:
        return f"Fehler bei Funktionsauflösung: {e}"

    # -----------------------------
    # 1.6 Auto-Solve & Syntax Check
    # -----------------------------
    
    if 'nsolve' in ausdruck and '=' in ausdruck:
        match_str, _, _ = extract_balanced_call(ausdruck, 'nsolve')
        if match_str and '=' in ausdruck.replace(match_str, ''):
            return "Fehler: Die Gleichung muss INNERHALB der Klammer von nsolve stehen."

    if '=' in ausdruck and not any(op in ausdruck for op in ['==', '!=', '>=', '<=', 'def ', 'nsolve', 'lsolve']):
        ausdruck = f"nsolve({ausdruck})"

    ausdruck = re.sub(r"root\(([^;]+);([^)]+)\)", r"(\1 ** (1/(\2)))", ausdruck)
    ausdruck = replace_factorials(ausdruck)
    
    def parse_vector(match):
        content = match.group(1).replace(';', ',')
        return f"Vector([{content}])"
    ausdruck = re.sub(r'\[([^\]]+)\]', parse_vector, ausdruck)

    def parse_stats(match):
        func_name = match.group(1)
        content = match.group(2).replace(';', ',')
        return f"{func_name}({content})"
    ausdruck = re.sub(r'(min|max|mittel|sd|binco|binom|cbinom)\(([^)]+)\)', parse_stats, ausdruck)

    ausdruck = apply_implicit_multiplication(ausdruck)
    ausdruck = ausdruck.replace("^", "**")
    ausdruck = re.sub(r'log\(([^;]+);([^)]+)\)', r'log(\1,\2)', ausdruck)

    # -----------------------------
    # 2. Spezial-Parser (Ableitung/Solver)
    # -----------------------------
    def solve_derivative(args_str, mode='value'):
        try:
            parts = [p.strip() for p in args_str.split(';')]
            if not parts or parts == ['']: return "'Fehler: Leere Eingabe für Ableitung'"
            
            func_def = parts[0]
            var_symbol = sp.Symbol('x')
            expression = None
            
            if '=' in func_def:
                lhs, rhs = func_def.split('=')
                var_match = re.search(r'\((.+)\)', lhs)
                if var_match:
                    var_symbol = sp.Symbol(var_match.group(1))
                expression = sp.sympify(rhs.replace('^', '**'))
            else:
                expression = sp.sympify(func_def.replace('^', '**'))
                free_syms = sorted(list(expression.free_symbols), key=lambda s: s.name)
                if free_syms: var_symbol = free_syms[0]

            if mode == 'value':
                if len(parts) < 3: return "'Fehler: Benötigt (Funktion; Stelle; Grad)'"
                pos_val = float(sp.sympify(parts[1]).evalf())
                order = int(parts[2])
                res = sp.diff(expression, var_symbol, order).subs(var_symbol, pos_val)
                return str(float(res.evalf()))
            elif mode == 'func':
                if len(parts) < 2: return "'Fehler: Benötigt (Funktion; Grad)'"
                order = int(parts[1])
                return f"'{str(sp.diff(expression, var_symbol, order))}'"

        except Exception as e:
            return f"'Ableitungsfehler: {str(e)}'"

    while True:
        match_str, content, _ = extract_balanced_call(ausdruck, 'nderive')
        if not match_str: break
        replacement = solve_derivative(content, mode='value')
        ausdruck = ausdruck.replace(match_str, replacement)

    while True:
        match_str, content, _ = extract_balanced_call(ausdruck, 'algs')
        if not match_str: break
        replacement = solve_derivative(content, mode='func')
        ausdruck = ausdruck.replace(match_str, replacement)

    # -----------------------------
    # 3. Vector Klasse
    # -----------------------------
    class Vector:
        def __init__(self, data):
            self.data = [float(x) for x in data]
        def __repr__(self): return f"Vector({self.data})"
        def __len__(self): return len(self.data)
        def __getitem__(self, key): return self.data[key]
        def __add__(self, o): return Vector([a + b for a, b in zip(self.data, o.data)]) if isinstance(o, Vector) else NotImplemented
        def __sub__(self, o): return Vector([a - b for a, b in zip(self.data, o.data)]) if isinstance(o, Vector) else NotImplemented
        def __mul__(self, o):
            if isinstance(o, Vector): return sum(a * b for a, b in zip(self.data, o.data))
            if isinstance(o, (int, float)): return Vector([x * o for x in self.data])
            return NotImplemented
        def __rmul__(self, o): return self.__mul__(o)
        def __truediv__(self, o): return Vector([x / o for x in self.data]) if isinstance(o, (int, float)) else NotImplemented
        def magnitude(self): return math.sqrt(sum(x**2 for x in self.data))

    # -----------------------------
    # 4. Hilfsfunktionen
    # -----------------------------
    def flatten_args(args):
        data = []
        for arg in args:
            if isinstance(arg, Vector): data.extend(arg.data)
            elif isinstance(arg, (list, tuple)): data.extend(flatten_args(arg))
            else: data.append(float(arg))
        return data
    
    def stat_min(*args): return min(flatten_args(args)) if args else 0
    def stat_max(*args): return max(flatten_args(args)) if args else 0
    def stat_mean(*args): 
        d = flatten_args(args)
        return sum(d)/len(d) if d else 0
    def stat_stdev(*args): 
        d = flatten_args(args)
        if len(d) < 1: return 0.0
        mu = sum(d)/len(d)
        return math.sqrt(sum((x-mu)**2 for x in d)/len(d))

    def require_integer(value, name):
        try:
            numeric = float(value)
        except Exception:
            raise ValueError(f"{name} muss eine ganze Zahl sein.")

        if not numeric.is_integer():
            raise ValueError(f"{name} muss eine ganze Zahl sein.")
        return int(numeric)

    def factorial_strict(x):
        n = require_integer(x, "Fakultät")
        if n < 0:
            raise ValueError("Fakultät ist nur für nichtnegative ganze Zahlen definiert.")
        return math.factorial(n)

    def binco(n, k):
        n_int = require_integer(n, "n")
        k_int = require_integer(k, "k")
        if n_int < 0:
            raise ValueError("n muss eine nichtnegative ganze Zahl sein.")
        if k_int < 0 or k_int > n_int:
            raise ValueError("k muss zwischen 0 und n liegen.")
        return math.comb(n_int, k_int)

    def binom(n, p, k):
        n_int = require_integer(n, "n")
        k_int = require_integer(k, "k")
        p_float = float(p)

        if n_int < 0:
            raise ValueError("n muss eine nichtnegative ganze Zahl sein.")
        if k_int < 0 or k_int > n_int:
            raise ValueError("k muss zwischen 0 und n liegen.")
        if not 0 <= p_float <= 1:
            raise ValueError("p muss zwischen 0 und 1 liegen.")

        return binco(n_int, k_int) * (p_float ** k_int) * ((1 - p_float) ** (n_int - k_int))

    def cbinom(n, p, k):
        n_int = require_integer(n, "n")
        k_int = require_integer(k, "k")
        p_float = float(p)

        if n_int < 0:
            raise ValueError("n muss eine nichtnegative ganze Zahl sein.")
        if k_int < 0 or k_int > n_int:
            raise ValueError("k muss zwischen 0 und n liegen.")
        if not 0 <= p_float <= 1:
            raise ValueError("p muss zwischen 0 und 1 liegen.")

        return sum(binom(n_int, p_float, i) for i in range(k_int + 1))

    def to_rad(x): return math.radians(x) if angle_mode == 'deg' else x
    def from_rad(x): return math.degrees(x) if angle_mode == 'deg' else x

    def vector_len_func(obj):
        if isinstance(obj, Vector): return obj.magnitude()
        if isinstance(obj, list): return math.sqrt(sum(v**2 for v in obj))
        try: return len(obj)
        except: return 0

    def cross(vec1, vec2):
        if not isinstance(vec1, Vector): vec1 = Vector(vec1)
        if not isinstance(vec2, Vector): vec2 = Vector(vec2)
        if len(vec1) != 3 or len(vec2) != 3: raise ValueError("Kreuzprodukt nur für 3D-Vektoren")
        return Vector([vec1[1]*vec2[2]-vec1[2]*vec2[1], vec1[2]*vec2[0]-vec1[0]*vec2[2], vec1[0]*vec2[1]-vec1[1]*vec2[0]])

    def dot(vec1, vec2): return Vector(vec1) * Vector(vec2)

    # -----------------------------
    # 5. Solver (nsolve, lsolve)
    # -----------------------------
    def nsolve(equation_str, *args):
        try:
            local_env = {'e': sp.E, 'pi': sp.pi, 'exp': sp.exp}

            if '=' in equation_str:
                left, right = equation_str.split('=')
                eq = sp.Eq(sp.sympify(left, locals=local_env), sp.sympify(right, locals=local_env))
            else:
                eq = sp.sympify(equation_str, locals=local_env)

            free_symbols = eq.free_symbols
            if not free_symbols: return "Keine Variable gefunden"
            variable = sorted(list(free_symbols), key=lambda s: s.name)[0]

            found_values = []
            
            # Numerisch
            guesses = [0, 1, 10, -10, 100, -100, 0.1, -0.1, 0.5, 50, -50]
            for guess in guesses:
                try:
                    sol_num = sp.nsolve(eq, variable, guess)
                    val = float(sol_num)
                    is_new = True
                    for existing in found_values:
                        if abs(existing - val) < 1e-6:
                            is_new = False
                            break
                    if is_new: found_values.append(val)
                except: continue

            # Symbolischer Fallback (sicherer)
            if not found_values:
                try:
                    eq_rational = sp.nsimplify(eq, rational=True)
                    solutions = sp.solve(eq_rational, variable, dict=False)
                    if solutions:
                        if isinstance(solutions, dict): sol_list = [solutions[variable]]
                        elif isinstance(solutions, list): sol_list = solutions
                        else: sol_list = [solutions]

                        for sol in sol_list:
                            try:
                                val = float(sol.evalf())
                                found_values.append(val)
                            except: pass
                except: pass

            if not found_values: return "Keine Lösung"

            # Formatierung via format_result (manuell hier, da nsolve String zurückgibt)
            formatted = []
            found_values.sort()
            seen_final = set()
            
            for val in found_values:
                if abs(val) < 10**(-decimals-2): val_chk = 0.0
                else: val_chk = round(val, decimals)
                
                if val_chk in seen_final: continue
                seen_final.add(val_chk)
                
                formatted.append(format_result(val_chk))
                
            return "; ".join(formatted) if formatted else "Keine reelle Lösung"

        except Exception as e:
            return f"Lösungsfehler: {e}"

    def lsolve(eqs_str):
        try:
            eqs_list = [e.strip() for e in eqs_str.split(';')]
            eqs_sympy = []
            vars_set = set()
            local_env = {'e': sp.E, 'pi': sp.pi}
            
            for eq_txt in eqs_list:
                if '=' not in eq_txt: continue
                l, r = eq_txt.split('=')
                l_ex = sp.sympify(l, locals=local_env)
                r_ex = sp.sympify(r, locals=local_env)
                eqs_sympy.append(sp.Eq(l_ex, r_ex))
                vars_set.update(l_ex.free_symbols | r_ex.free_symbols)
            
            vars_list = sorted(vars_set, key=lambda x: x.name)
            if not vars_list: return "Keine Variablen für System gefunden."
            
            sol = sp.linsolve(eqs_sympy, vars_list)
            if not sol: return "Keine eindeutige Lösung."
            
            sol_tuple = list(sol)[0]
            res = []
            for v, val in zip(vars_list, sol_tuple):
                val_f = float(val.evalf())
                res.append(f"{v}={format_result(val_f)}")
            return "; ".join(res)
        except Exception as e:
            return f"Systemfehler: {e}"

    # Solver in String verpacken
    while True:
        match_str, content, _ = extract_balanced_call(ausdruck, 'nsolve')
        if not match_str: break
        ausdruck = ausdruck.replace(match_str, f'__nsolve_calc("{content}")')

    while True:
        match_str, content, _ = extract_balanced_call(ausdruck, 'lsolve')
        if not match_str: break
        ausdruck = ausdruck.replace(match_str, f'__lsolve_calc("{content}")')

    erlaubte_namen = {
        "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
        "sin": lambda x: math.sin(to_rad(x)),
        "cos": lambda x: math.cos(to_rad(x)),
        "tan": lambda x: math.tan(to_rad(x)),
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        # Hyperbolische Funktionen (NEU)
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
        
        "ln": math.log, "lg": math.log10, "log": math.log,
        "__nsolve_calc": nsolve, "__lsolve_calc": lsolve,
        "nsolve": nsolve, "lsolve": lsolve,
        "factorial_strict": factorial_strict,
        "binco": binco, "binom": binom, "cbinom": cbinom,
        "Vector": Vector, "len": vector_len_func,
        "cross": cross, "dot": dot, "abs": abs,
        "min": stat_min, "max": stat_max, "mittel": stat_mean, "sd": stat_stdev
    }

    # -----------------------------
    # EVALUIERUNG & FEHLERBEHANDLUNG (NEU)
    # -----------------------------
    try:
        ergebnis = eval(ausdruck, {"__builtins__": None}, erlaubte_namen)
        
        # HIER: Finale Formatierung für ALLES (Zahlen, Vektoren, Strings von 'algs')
        return format_result(ergebnis)

    except SyntaxError:
        return "Syntaxfehler: Bitte überprüfen Sie Klammern und Rechenzeichen."
    except ZeroDivisionError:
        return "Mathematischer Fehler: Division durch Null ist nicht erlaubt."
    except NameError as e:
        # Versuch, den unbekannten Namen aus der Fehlermeldung zu holen
        msg = str(e)
        match = re.search(r"name '([^']+)' is not defined", msg)
        name = match.group(1) if match else "Variable/Funktion"
        return f"Fehler: '{name}' ist unbekannt. Tippfehler?"
    except ValueError as e:
        msg = str(e)
        if "math domain error" in msg:
            return "Wertefehler: Ungültige Eingabe (z.B. Wurzel aus negativer Zahl oder acosh(x<1))."
        return f"Wertefehler: {msg}"
    except TypeError:
        return "Typfehler: Falscher Datentyp oder falsche Anzahl an Argumenten."
    except OverflowError:
        return "Fehler: Das Ergebnis ist zu groß für die Berechnung."
    except Exception as e:
        return f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
