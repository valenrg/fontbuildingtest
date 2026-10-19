# Mirrorball

Mirrorball is an original typeface in the tight geometric-grotesque genre
with a seventies disco flavour: flat and radially cut terminals, a big
x-height, square dots, close spacing, and a weight range from Hairline to
Poster. It ships as OTF, TTF and WOFF2.

![Specimen](specimen/specimen.png)

| Style | Stroke (units) | OS/2 weight |
|---|---|---|
| Hairline | 20 | 100 |
| Light | 60 | 300 |
| Regular | 95 | 400 |
| Bold | 150 | 700 |
| Poster | 200 | 900 |

## How it is made

Every glyph is drawn once as a **stroke skeleton** of straight lines and
circular arcs (`tools/glyphs.py`). The engine in `tools/stroke.py` expands
the skeleton into flat-ended bands, merges the pieces with a boolean union,
and subtracts optional cut polygons to clip apexes, corners and terminals
flat or to carve apertures. One set of drawings yields every weight: only
the stroke width changes.

* Line and arc offsets are exact (parallel lines, concentric arcs), so the
  outlines are clean cubic curves rather than flattened polygons.
* Radii are expressed as *outer* radii minus the half stroke, so the
  silhouette holds across weights while the counters shrink; the heavy
  weights also get extra width (`Ctx.ex`) so counters survive.
* Horizontals thin slightly as weight grows, and the parts that would close
  a counter (the bar of `e`, the bowl of `a`, the hook of `g`) thin further.
* Every boolean union is validated (area, bounds and skeleton probe points)
  and retried with an invisible nudge if Skia trips on coincident geometry.

## Build

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python tools/build.py              # UFO masters -> fonts/*.otf|ttf|woff2 + specimen
python tools/build.py --no-compile # only regenerate build/masters/*.ufo
python tools/closeup.py out.png "a e g s" "Shortcircuit"   # close-up proof
```

Outputs go to `fonts/`; intermediate UFO masters go to `build/masters/`.
Open `specimen/index.html` in a browser for a live specimen.

## Metrics

| | units |
|---|---|
| UPM | 1000 |
| x-height | 520 |
| cap height | 700 |
| ascender | 720 |
| descender | -190 |

## Character set

Basic Latin (A–Z, a–z, 0–9), common punctuation and symbols, curly single
and double quotes, en/em dash, multiply, minus, inverted ! and ?. A small
`kern` feature covers the diagonal capitals and a few lowercase pairs.

## Licence

Not yet decided; the copyright line in the fonts names "The Mirrorball
Project Authors". Pick a licence (for example the SIL Open Font License)
before distributing.
