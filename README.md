# Graufieber

Ein Abenteuer für *The One Ring, 2nd Edition* · Küste von Belfalas, Spätsommer TA 2979.

Ein One-Shot für 3–4 Spieler (5–6 Stunden) im Süden von Gondor: Der Truchsess schickt die Helden von Minas Tirith aus nach Süden. Die Handlung ist frei nach dem
Arma-3-Szenario *Old Man* erzählt: Die „Helfer“ eines Handelshauses, hinter dem ein Schwarzer
Númenórer aus Umbar steht, säen in einem Hafenort an der Küste von Belfalas ein Fieber, und am Ende
entscheiden die Helden, wer das einzige Gegenmittel bekommt.

Dieses Repository enthält den Text des Abenteuers und die Pipeline, die daraus die
Druckfassung baut. Sie ist von [tor2e-finsterwacht](https://github.com/Andx667/tor2e-finsterwacht)
übernommen. Bei jedem Commit baut GitHub Actions die PDFs (Reiter **Actions** → letzter Lauf →
Artefakte `Graufieber-TOR2e-DE-v….pdf` und `Graufieber-TOR2e-DE-Buch-v….pdf`).

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `src/graufieber.md` | Der Abenteuertext (Pandoc-Markdown) – hier wird geschrieben |
| `NOTICE.md` | Wem die Namen und Inhalte gehören und was die MIT-Lizenz abdeckt |
| `assets/maps/` | Die gezeichneten Karten als JPG, Quellen als SVG in `svg/` |
| `assets/route-de.*` | Das Routendiagramm im Überblick |
| `latex/graufieber.sty` | Das Layout: Ränder, Notizspalte, Kästen, Tabellen, Karten, Handouts |
| `latex/graufieber.tex` | Gerüst der Blattfassung (einseitig, links gelocht) |
| `latex/graufieber-buch.tex` | Gerüst der Buchfassung (Buchblock zum Binden) |
| `latex/inhalt.tex` | Inhalt beider Fassungen (Titel, Karten, Handouts) |
| `filters/graufieber.lua` | Pandoc-Filter: Markdown-Elemente → Layout-Bausteine |
| `tools/build.py` | Baut das PDF |
| `tools/maps.py` | Zeichnet Karten und Routendiagramm neu (optional, braucht Playwright und Pillow) |
| `.github/workflows/build.yml` | CI: baut das PDF bei jedem Commit |

## Schreibregeln im Markdown

- `## Kapitel {#id}` beginnt ein Kapitel auf neuer Seite mit Notizspalte;
  `{#id .nonotes}` setzt es ohne Notizspalte in voller Breite.
- `### Abschnitt` ist eine Zwischenüberschrift.
- Absätze, die mit einem dieser fetten Labels beginnen, werden zu Kästen:
  **Hinweis für den Loremaster:**, **Optionale Erweiterung – …:**,
  **Erinnerung für den Loremaster – …:**, **Möglicher Abschluss:**,
  **Wenn sie …:** (z. B. **Wenn sie trotzdem gehen:**), **Erfahrung:**
- Ein Absatz **Hausregel – …:** mit folgender Liste und folgendem Absatz wird zum
  gerahmten Hausregel-Kasten.
- Die Wörter `Optional` und `Überspringbar` werden zur grauen Markierung.
- Karten im Text: `![Bildunterschrift](assets/maps/datei.jpg){.map}`,
  das Routendiagramm mit `{.route}`.
- Briefe: `::: {.letter #id} … :::` mit `\` am Zeilenende und `[Unterschrift]{.sig}`;
  sie erscheinen im Text und zusätzlich als Handout-Seite (`\fwhandoutletter` in `latex/inhalt.tex`).
- Tabellen: normale Pipe-Tabellen; die Spaltenbreiten richten sich nach dem ersten
  Spaltenkopf (siehe `TABLES` im Filter).
- Regelbegriffe kursiv (`*Insight*`), Tolkien-Namen und Regelbegriffe bleiben englisch.

## Version und Stand

Version und Datum in der Fußzeile kommen aus git: die Nummer des letzten Tags (`v1.0` →
**Version 1.0**) und das Datum des letzten Commits. Der Dateiname nennt die genaue Version
(`…-v1.0.pdf`, danach `…-v1.0+3-abc1234.pdf`). Ein Tag `v*` erzeugt zusätzlich ein
GitHub-Release mit beiden PDFs:

```sh
git tag v1.1
git push --tags
```

## Blattfassung und Buchfassung

- **Blattfassung** (`Graufieber-TOR2e-DE-v….pdf`): lose Blätter für den Ordner, 26 mm Rand
  links für die Lochung, Karten und Handouts im Querformat.
- **Buchfassung** (`Graufieber-TOR2e-DE-Buch-v….pdf`): Buchblock zum Binden, doppelseitig;
  Querseiten stehen gedreht, Notizseiten füllen auf eine durch 4 teilbare Seitenzahl auf.

## Lokal bauen

Voraussetzungen: TeX Live mit LuaLaTeX und `latexmk`, `pandoc`, Python 3.

```sh
make            # beide Fassungen; oder: python3 tools/build.py
make buch       # nur eine Fassung (blatt | buch)
make maps       # Karten neu zeichnen
```

Fehlt LuaLaTeX (`luaotfload`), nimmt das Skript ersatzweise XeLaTeX; fehlen die deutschen
Trennmuster, setzt es Flattersatz. Maßgeblich ist der CI-Build.

## Lizenz und Rechte

„Graufieber“ ist ein **inoffizielles Fanwerk**, nicht verbunden mit oder gebilligt von
Middle-earth Enterprises, der Tolkien Estate, Sophisticated Games, Free League Publishing oder
Bohemia Interactive. Siehe [NOTICE.md](NOTICE.md). Das Abenteuer darf nicht verkauft werden.

Code, Layout, Karten und der eigene Text stehen unter der MIT-Lizenz, siehe [LICENSE](LICENSE).

## Geschichte

Der erste Entwurf entstand als Claude-Doc (noch in Tharbad, mit Saruman als Gegenspieler).
Version 1.0 übernahm diese Fassung; ab Version 1.1 spielt das Abenteuer an der Küste von Belfalas.
Dieses Repository ist die maßgebliche Quelle.
