import re, subprocess, sys, tempfile, pathlib
root = pathlib.Path(__file__).parent
errors = []
for f in sorted(root.glob("v*/index.html")):
    d = f.parent
    if not (d / "notes.md").exists():
        errors.append(f"{d.name}: missing notes.md")
    for ref in re.findall(r'(?:src|href)="(\.\./shared/[^"]+)"', f.read_text()):
        if not (d / ref).exists():
            errors.append(f"{d.name}: missing {ref}")
    text = f.read_text()
    for i, m in enumerate(re.finditer(r"<script(?![^>]*src)[^>]*>(.*?)</script>", text, re.S)):
        js = m.group(1).strip()
        if not js:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
            t.write(js); name = t.name
        r = subprocess.run(["node", "--check", name], capture_output=True, text=True)
        if r.returncode != 0:
            errors.append(f"{d.name} script#{i}: {r.stderr.strip()[:300]}")
for shared in sorted(root.glob("shared/*.js")):
    r = subprocess.run(["node", "--check", str(shared)], capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"{shared.name}: {r.stderr.strip()[:300]}")
print("\n".join(errors) if errors else "ALL OK")
sys.exit(1 if errors else 0)
