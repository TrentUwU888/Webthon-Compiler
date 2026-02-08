import os
import re
import sys
import textwrap
import subprocess

def syntax():
    """
    Only converts WebThon-specific tags to HTML.
    Normal HTML is left untouched.
    """
    return {
        "<css>": "<style>",
        "</css>": "</style>",
        "<js>": "<script>",
        "</js>": "</script>",
    }

def compile_webthon_file(source_file: str, html_output: str, c_folder: str, python_folder: str) -> None:
    if not os.path.isfile(source_file):
        raise FileNotFoundError(f"Source file '{source_file}' does not exist.")

    with open(source_file, "r") as f:
        code = f.read()

    # -------------------------
    # Extract C code blocks
    # -------------------------
    c_blocks = re.findall(r"<c>(.*?)</c>", code, re.DOTALL)
    for i, block in enumerate(c_blocks, start=1):
        clean_block = textwrap.dedent(block).strip()
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        c_file = os.path.join(c_folder, f"{base_name}_c_{i}.c")

        with open(c_file, "w") as cf:
            cf.write(clean_block)

        print(f"Extracted C code to {c_file}")

        # Compile and run automatically
        exe_file = c_file.replace(".c", "")
        try:
            subprocess.run(["gcc", c_file, "-o", exe_file], check=True)
            print(f"Compiled {c_file} → {exe_file}")
            subprocess.run([exe_file])
        except subprocess.CalledProcessError as e:
            print(f"Error compiling C code: {e}")

    code = re.sub(r"<c>.*?</c>", "", code, flags=re.DOTALL)

    # -------------------------
    # Extract Python blocks
    # -------------------------
    python_blocks = re.findall(r"<python>(.*?)</python>", code, re.DOTALL)
    for i, block in enumerate(python_blocks, start=1):
        clean_block = textwrap.dedent(block).strip()
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        python_file = os.path.join(python_folder, f"{base_name}_py_{i}.py")

        with open(python_file, "w") as pf:
            pf.write(clean_block)

        print(f"Extracted Python code to {python_file}")

        # Run Python in separate process (Tkinter, Pygame works)
        try:
            print("Launching Python program...")
            subprocess.run(["python3", python_file])
        except Exception as e:
            print(f"Error executing Python code: {e}", file=sys.stderr)

    code = re.sub(r"<python>.*?</python>", "", code, flags=re.DOTALL)

    # -------------------------
    # Replace WebThon tags (<css> & <js>)
    # -------------------------
    for tag, html in syntax().items():
        code = code.replace(tag, html)

    # Remove <webthon> wrapper if present
    code = code.replace("<webthon>", "")
    code = code.replace("</webthon>", "")

    # -------------------------
    # Wrap in full HTML
    # -------------------------
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{os.path.basename(source_file)}</title>
</head>
<body>
{code}
</body>
</html>
"""

    with open(html_output, "w") as f:
        f.write(html_content)

    print(f"Compiled {source_file} to HTML: {html_output}")

    # Open HTML automatically in browser
    try:
        print("Opening HTML in browser...")
        subprocess.run(["xdg-open", html_output])
    except Exception as e:
        print(f"Could not open browser: {e}")

def compile_all_webthon(program_folder: str):
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
        html_output = os.path.join(
            program_folder,
            f"{os.path.splitext(wth_file)[0]}.html"
        )

        compile_webthon_file(source_path, html_output, c_folder, python_folder)

if __name__ == "__main__":
    program_folder = "/home/trenton/Webthon/Webthon Programs"
    compile_all_webthon(program_folder)
