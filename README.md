# Recursive Charon

A customized fork of [Recursive Sans & Mono](https://github.com/arrowtype/recursive) adapted to match the proportions of Iosevka Charon — and **extended far past what the base Recursive font offers** by borrowing glyph coverage from [Iosevka Charon](https://github.com/jul-sh/iosevka-charon).

## Extended character coverage

The upstream Recursive font covers only around 745 codepoints — essentially Latin plus a handful of symbols. Recursive Charon extends this to the full ~7,500-codepoint repertoire of [Iosevka Charon](https://github.com/jul-sh/iosevka-charon): extended Latin, Greek, Cyrillic, rich punctuation, arrows, and technical symbols.

The rule is simple: **wherever Recursive Charon draws a character, its own glyph is used; every character it lacks is filled in from Iosevka Charon.** Because both families are TrueType at 1000 units-per-em (and both mono variants share a 500-unit cell), glyphs are borrowed verbatim, with no scaling. Borrowed accented and composite letters are even rebuilt on top of Recursive's own base shapes where possible, so they stay visually on-brand.

This happens automatically at build time — see [`mastering/extend_charon.py`](mastering/extend_charon.py). To pull a newer Iosevka Charon release, bump the single `IOSEVKA_CHARON_VERSION` constant at the top of that file to a tag from the [Iosevka Charon releases](https://github.com/jul-sh/iosevka-charon/releases) and rebuild; the matching release is downloaded and cached automatically.

## What changed

### Narrower character cell

The monospace cell width was compressed from 600 units to 500 units (a ~17% reduction), bringing it in line with Iosevka Charon's proportions. All horizontal coordinates, advance widths, component offsets, anchors, guidelines, kerning, and stem snap values were scaled accordingly. Vertical metrics were left untouched.

### Rounder dots

Dot contours across the family (period, ellipsis, question mark, dot accents) were replaced with proper circular Bezier curves. Rounded dots from the Casual masters were also propagated to the Linear masters for consistency. Dots on `i` and `j` were shrunk by 20%.

### Default stylistic sets

Several stylistic sets are enabled by default via contextual alternates: `ss02`, `ss04`, `ss05`, `ss06`, `ss07`, `ss08`, and `ss12`.

### Cursive default

The `CRSV` (Cursive) axis default was changed from `0.5` (auto) to `1` (always cursive).

### Design fixes

- Fixed italic `f` rendering across all masters
- Fixed top-bar overhangs on B, R, F, P, E, D, J
- Corrected Cursive axis coordinates
- Flattened weight scaling
- Improved macOS Font Book display via STAT table elidable flags

## Variable axes

Same as the original Recursive, with the noted default change on the Cursive axis:

| Axis      | Tag    | Range       | Default | Description                          |
| --------- | ------ | ----------- | ------- | ------------------------------------ |
| Monospace | `MONO` | 0 to 1      | 0       | Sans (proportional) to Mono (fixed)  |
| Casual    | `CASL` | 0 to 1      | 0       | Linear to Casual                     |
| Weight    | `wght` | 300 to 1000 | 300     | Light to ExtraBlack                  |
| Slant     | `slnt` | 0 to -15    | 0       | Upright to Slanted (~15 degrees)     |
| Cursive   | `CRSV` | 0, 0.5, 1   | **1**   | Roman (0), auto (0.5), cursive (1)   |

## Installing

On macOS, fonts downloaded from GitHub (including CI artifacts) are flagged by Gatekeeper. After unzipping, strip the quarantine attribute before installing:

```bash
xattr -dr com.apple.quarantine ~/Downloads/recursive-charon-fonts-*/
```

## Building

Fonts are built automatically via GitHub Actions on push to `main`. To build locally:

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -U -r requirements.txt
cd mastering
python build.py --all --version 1.085
```

## License

Licensed under the [SIL Open Font License v1.1](OFL.txt), same as the original Recursive.

## Credits

- Original [Recursive](https://github.com/arrowtype/recursive) design by Stephen Nixon / [Arrow Type](https://arrowtype.com)
- Charon modifications by Juliette Pluto
