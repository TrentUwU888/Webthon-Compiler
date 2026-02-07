import os
import subprocess
import sys

# -------------------------------
# Node classes for AST
# -------------------------------
class Node:
    pass

class TextNode(Node):
    def __init__(self, text):
        self.text = text

class HtmlTagNode(Node):
    def __init__(self, tag, children=None):
        self.tag = tag
        self.children = children or []

class PythonNode(Node):
    def __init__(self, code):
        self.code = code

class CNode(Node):
    def __init__(self, code):
        self.code = code

# -------------------------------
# Lexer / Tokenizer
# -------------------------------
import re

TOKEN_REGEX = re.compile(r"(<.*?>)|([^<>]+)", re.DOTALL)

def tokenize(source):
    tokens = []
    for match in TOKEN_REGEX.finditer(source):
        if match.group(1):
            tokens.append(('TAG', match.group(1)))
        else:
            tokens.append(('TEXT', match.group(2)))
    return tokens

# -------------------------------
# Parser
# -------------------------------
HTML_TAGS = {
    "<print>": "<h1>", "</print>": "</h1>",
    "<css>": "<style>", "</css>": "</style>",
    "<js>": "<script>", "</js>": "</script>"
}

def parse(tokens):
    stack = [HtmlTagNode("root", [])]
    i = 0
    while i < len(tokens):
        token_type, value = tokens[i]

        if token_type == "TEXT":
            stack[-1].children.append(TextNode(value))
        elif token_type == "TAG":
            # Python block
            if value == "<python>":
                code = ""
                i += 1
                while i < len(tokens) and tokens[i][1] != "</python>":
                    code += tokens[i][1]
                    i += 1
                stack[-1].children.append(PythonNode(code.strip()))
            # C block
            elif value == "<c>":
                code = ""
                i += 1
                while i < len(tokens) and tokens[i][1] != "</c>":
                    code += tokens[i][1]
                    i += 1
                stack[-1].children.append(CNode(code.strip()))
            # HTML tags
            elif value in HTML_TAGS:
                tag = HTML_TAGS[value]
                node = HtmlTagNode(tag, [])
                stack[-1].children.append(node)
                # if it's an opening tag
                if not value.startswith("</"):
                    stack.append(node)
            elif value in HTML_TAGS.values():
                pass  # ignore already converted closing tags
            elif value.startswith("</"):  # closing HTML tag
                if len(stack) > 1:
                    stack.pop()
        i += 1
    return stack[0]

# -------------------------------
# Code generation
# -------------------------------
def generate_html(node):
    if isinstance(node, TextNode):
        return node.text
    elif isinstance(node, HtmlTagNode):
        inner = "".join(generate_html(child) for child in node.children)
        if node.tag == "root":
            return inner
        return f"<{node.tag}>{inner}</{node.tag}>"
    elif isinstance(node, PythonNode):
        return f"<pre><code>{node.code}</code></pre>"
    elif isinstance(node, CNode):
        return f"<pre><code>{node.code}</code></pre>"
    return ""

def execute_nodes(node, c_folder, python_folder, source_file):
    for child in getattr(node, "children", []):
        if isinstance(child, PythonNode):
            python_file = os.path.join(python_folder, f"{os.path.splitext(os.path.basename(source_file))[0]}_py.py")
            with open(python_file, "w") as pf:
                pf.write(child.code)
            print(f"Extracted Python code to {python_file}")
            try:
                exec(child.code, {})
            except Exception as e:
                print(f"Error executing Python code: {e}", file=sys.stderr)
        elif isinstance(child, CNode):
            c_file = os.path.join(c_folder, f"{os.path.splitext(os.path.basename(source_file))[0]}_c.c")
            exe_file = os.path.join(c_folder, f"{os.path.splitext(os.path.basename(source_file))[0]}_c")
            with open(c_file, "w") as cf:
                cf.write(child.code)
            print(f"Extracted C code to {c_file}")
            try:
                subprocess.run(["gcc", c_file, "-o", exe_file], check=True)
                print(f"Compiled C code to executable: {exe_file}")
                result = subprocess.run([exe_file], capture_output=True, text=True)
                print(f"C output:\n{result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"Error compiling/running C code: {e}", file=sys.stderr)
        elif isinstance(child, HtmlTagNode):
            execute_nodes(child, c_folder, python_folder, source_file)

# -------------------------------
# Main compiler function
# -------------------------------
def compile_webthon_file(source_file, output_html, c_folder, python_folder):
    if not os.path.isfile(source_file):
        raise FileNotFoundError(f"Source file '{source_file}' does not exist.")

    with open(source_file, "r") as f:
        source = f.read()

    tokens = tokenize(source)
    ast = parse(tokens)
    execute_nodes(ast, c_folder, python_folder, source_file)
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{os.path.basename(source_file)}</title>
</head>
<body>
{generate_html(ast)}
</body>
</html>
"""
    with open(output_html, "w") as f:
        f.write(html_content)
    print(f"Compiled {source_file} to HTML: {output_html}")

# -------------------------------
# Compile all WebThon programs in a folder
# -------------------------------
def compile_all_webthon(program_folder):
    if not os.path.isdir(program_folder):
        raise NotADirectoryError(f"Folder '{program_folder}' does not exist.")

    c_folder = os.path.join(program_folder, "c_code")
    python_folder = os.path.join(program_folder, "python_code")
    os.makedirs(c_folder, exist_ok=True)
    os.makedirs(python_folder, exist_ok=True)

    wth_files = [f for f in os.listdir(program_folder) if f.endswith(".wth")]
    if not wth_files:
        print("No .wth files found.")
        return

    for wth_file in wth_files:
        source_path = os.path.join(program_folder, wth_file)
        html_output = os.path.join(program_folder, f"{os.path.splitext(wth_file)[0]}.html")
        compile_webthon_file(source_path, html_output, c_folder, python_folder)

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    program_folder = "/home/trenton/Webthon/Webthon Programs"
    compile_all_webthon(program_folder)
