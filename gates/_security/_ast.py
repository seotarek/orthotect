"""
Python AST analysis.

This is the only part of the gate that parses rather than pattern-matches, and
it exists because a regex cannot tell `subprocess.run(cmd, shell=True)` from the
same text inside a comment or a string. Findings here are structural.
"""
import ast

from ._patterns import CRITICAL, HIGH

def scan_python_ast(filepath, content):
    """Perform AST taint and syntax-level vulnerability checks on Python source code."""
    findings = []
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError:
        return findings

    # Import tracking for YAML modules, direct function imports, and custom aliases
    yaml_modules = {'yaml'}
    direct_unsafe_calls = {'unsafe_load'}
    direct_load_calls = {'load'}
    safe_loader_names = {'SafeLoader', 'CSafeLoader'}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'yaml' and alias.asname:
                    yaml_modules.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module == 'yaml':
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    if alias.name == 'unsafe_load':
                        direct_unsafe_calls.add(local_name)
                    elif alias.name == 'load':
                        direct_load_calls.add(local_name)
                    elif alias.name in ('SafeLoader', 'CSafeLoader'):
                        safe_loader_names.add(local_name)

    for node in ast.walk(tree):
        # 1. SQL Injection via formatted strings in cursor.execute
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
                
            if func_name in ('execute', 'executemany'):
                if node.args:
                    first_arg = node.args[0]
                    # f-string: ast.JoinedStr
                    if isinstance(first_arg, ast.JoinedStr):
                        findings.append((
                            first_arg.lineno,
                            "SQL Injection: Raw formatted f-string passed to database execute() sink",
                            CRITICAL,
                            "cursor.execute(f\"...\")"
                        ))
                    # % formatting or string concatenation
                    elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, (ast.Mod, ast.Add)):
                        findings.append((
                            first_arg.lineno,
                            "SQL Injection: String concatenation or % formatting passed to database execute() sink",
                            CRITICAL,
                            "cursor.execute(... + ...)"
                        ))

            # 2. Subprocess with shell=True
            if func_name in ('Popen', 'call', 'run', 'check_call', 'check_output'):
                for kw in node.keywords:
                    if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append((
                            node.lineno,
                            "OS Command Injection: subprocess invocation with shell=True",
                            HIGH,
                            f"subprocess.{func_name}(..., shell=True)"
                        ))

            # 3. Insecure pickle loads
            if func_name in ('load', 'loads') and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pickle':
                    findings.append((
                        node.lineno,
                        "Insecure Deserialization: Untrusted pickle.loads() execution",
                        CRITICAL,
                        "pickle.loads(...)"
                    ))

            # 4. Insecure yaml.load / yaml.unsafe_load (with full alias & direct import support)
            is_yaml_call = False
            is_unsafe_call = False
            is_load_call = False

            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id in yaml_modules:
                    if node.func.attr == 'unsafe_load':
                        is_yaml_call = True
                        is_unsafe_call = True
                    elif node.func.attr == 'load':
                        is_yaml_call = True
                        is_load_call = True
            elif isinstance(node.func, ast.Name):
                if node.func.id in direct_unsafe_calls:
                    is_yaml_call = True
                    is_unsafe_call = True
                elif node.func.id in direct_load_calls:
                    is_yaml_call = True
                    is_load_call = True

            if is_yaml_call:
                if is_unsafe_call:
                    findings.append((
                        node.lineno,
                        "Insecure Deserialization: yaml.unsafe_load allows arbitrary code execution",
                        CRITICAL,
                        "unsafe_load(...)"
                    ))
                elif is_load_call:
                    loader_kw = next((kw for kw in node.keywords if kw.arg == 'Loader'), None)
                    loader_safe = False
                    if loader_kw:
                        val = loader_kw.value
                        if isinstance(val, ast.Name) and val.id in safe_loader_names:
                            loader_safe = True
                        elif isinstance(val, ast.Attribute):
                            if (isinstance(val.value, ast.Name) and 
                                val.value.id in yaml_modules and 
                                val.attr in safe_loader_names):
                                loader_safe = True

                    if not loader_safe:
                        findings.append((
                            node.lineno,
                            "Insecure Deserialization: yaml.load without SafeLoader",
                            HIGH,
                            "yaml.load(...)"
                        ))

    return findings
