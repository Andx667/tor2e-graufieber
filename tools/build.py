#!/usr/bin/env python3
"""Baut die Druckfassung von „Graufieber“.

    python3 tools/build.py            # beide Fassungen
    python3 tools/build.py buch       # nur eine: blatt | buch

Schritte:
  1. Version und Stand aus git (letztes Tag v*, Commit-Datum) -> build/version.tex
  2. src/graufieber.md -> build/body.tex (pandoc + filters/graufieber.lua);
     die Briefe gehen zusätzlich nach build/letters.tex (Handout-Seiten)
  3. LuaLaTeX (latexmk) -> build/Graufieber-TOR2e-DE.pdf (Blattfassung, gelocht)
     und build/Graufieber-TOR2e-DE-Buch.pdf (Buchfassung zum Binden)
  4. Kopie mit Version im Namen -> build/Graufieber-TOR2e-DE-v1.0.pdf

Benötigt: pandoc, LuaLaTeX mit latexmk (TeX Live), Python 3.
Ohne luaotfload wird ersatzweise XeLaTeX genutzt (FW_ENGINE=… erzwingt eine Engine).
"""
import datetime
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
JOB = "Graufieber-TOR2e-DE"
# Fassung -> (LaTeX-Gerüst, Jobname)
EDITIONS = {
    "blatt": ("latex/graufieber.tex", JOB),
    "buch": ("latex/graufieber-buch.tex", JOB + "-Buch"),
}


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True, **kw)


def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def version():
    """Die Version im PDF ist die Nummer des letzten Tags: v1.2 -> „1.2“.

    Dritter Rückgabewert ist die genaue Version für den Dateinamen: „v1.2“ auf dem
    getaggten Commit, drei Commits danach „v1.2+3-abc1234“.
    """
    desc = git("describe", "--tags", "--long", "--match", "v*")
    m = re.match(r"v(.+)-(\d+)-g([0-9a-f]+)$", desc)
    if m:
        ver = m[1]
        slug = "v" + (m[1] if m[2] == "0" else f"{m[1]}+{m[2]}-{m[3]}")
    else:
        commit = git("rev-parse", "--short", "HEAD")
        ver = "0.0"
        slug = "v0.0" + ("-" + commit if commit else "")
    if git("status", "--porcelain", "--untracked-files=no"):
        slug += "-lokal"
    stand = git("log", "-1", "--format=%cd", "--date=format:%d.%m.%Y") or datetime.date.today().strftime("%d.%m.%Y")
    return ver, stand, slug


def tex_escape(s):
    esc = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return re.sub(r"[\\&%$#_{}~^]", lambda m: esc[m[0]], s)


def main():
    editions = sys.argv[1:] or list(EDITIONS)
    for e in editions:
        if e not in EDITIONS:
            sys.exit(f"Unbekannte Fassung „{e}“ – möglich: " + ", ".join(EDITIONS))
    os.makedirs(BUILD, exist_ok=True)
    ver, stand, slug = version()
    with open(os.path.join(BUILD, "version.tex"), "w", encoding="utf-8") as f:
        f.write("\\def\\fwversion{%s}\n\\def\\fwstand{%s}\n" % (tex_escape(ver), stand))
    print(f"Version {ver} · Stand {stand}")

    env = dict(os.environ, FW_BUILD=BUILD)
    open(os.path.join(BUILD, "letters.tex"), "w").close()  # der Filter hängt jeden Brief an
    run(["pandoc", "src/graufieber.md", "-f", "markdown", "-t", "latex",
         "--lua-filter", "filters/graufieber.lua",
         "-o", os.path.join(BUILD, "body.tex")], env=env)

    env["TEXINPUTS"] = os.path.join(ROOT, "latex") + "//" + os.pathsep + env.get("TEXINPUTS", "")
    tex = ["-interaction=nonstopmode", "-halt-on-error", "-file-line-error"]
    # LuaLaTeX ist die Referenz (CI); fehlt luaotfload, ersatzweise XeLaTeX
    engine = os.environ.get("FW_ENGINE") or (
        "lualatex" if subprocess.run(["kpsewhich", "luaotfload-main.lua"], capture_output=True, text=True).stdout.strip()
        else "xelatex")
    print("TeX-Engine:", engine)
    for e in editions:
        src, job = EDITIONS[e]
        if shutil.which("latexmk"):
            run(["latexmk", "-" + engine, "-outdir=build", "-jobname=" + job, *tex, src], env=env)
        else:  # ohne latexmk: drei Läufe reichen für Seitenverweise und Lesezeichen
            for _ in range(3):
                run([engine, *tex, "-output-directory=build", "-jobname=" + job, src], env=env)
        # Kopie mit Version im Dateinamen – diese Datei veröffentlicht die CI
        pdf = os.path.join("build", f"{job}-{slug}.pdf")
        shutil.copyfile(os.path.join(BUILD, job + ".pdf"), os.path.join(ROOT, pdf))
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("pdf=" + pdf.replace(os.sep, "/") + "\n")
        print("fertig:", pdf)


if __name__ == "__main__":
    sys.exit(main())
