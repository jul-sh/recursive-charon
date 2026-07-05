"""
Extend Recursive Charon with Iosevka Charon glyph coverage.

Recursive (and therefore Recursive Charon) only covers a few hundred
codepoints -- essentially Latin plus a handful of symbols. Iosevka Charon
(https://github.com/jul-sh/iosevka-charon) covers thousands of codepoints:
extended Latin, Greek, Cyrillic, punctuation, arrows, technical symbols, and
much more.

This module fills the gap: after the Recursive Charon fonts are built, every
codepoint that Recursive Charon does **not** cover is borrowed from the
matching Iosevka Charon font. Recursive Charon glyphs always win; Iosevka
Charon is used only as a fallback for characters Recursive never had.

Both families are TrueType (`glyf`) outlines at 1000 units-per-em, so glyphs
are copied verbatim with no scaling.

Updating to a newer Iosevka Charon release
------------------------------------------
Bump the single constant `IOSEVKA_CHARON_VERSION` below to the desired release
tag from https://github.com/jul-sh/iosevka-charon/releases and rebuild. The
matching release zip is downloaded and cached automatically. Nothing else in
this file, or the rest of the build, needs to change.
"""

import io
import os
import zipfile
import urllib.request

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable


# === Iosevka Charon source (bump this to update) ===========================

# Release tag from https://github.com/jul-sh/iosevka-charon/releases
IOSEVKA_CHARON_VERSION = "v34.300"

# The "general use" TrueType archive attached to every release.
_ASSET_NAME = "iosevka-charon.zip"
_RELEASE_URL = (
    "https://github.com/jul-sh/iosevka-charon/releases/download/"
    f"{IOSEVKA_CHARON_VERSION}/{_ASSET_NAME}"
)

# Where the downloaded/extracted Iosevka Charon fonts are cached. Keyed by
# version so bumping IOSEVKA_CHARON_VERSION transparently fetches fresh fonts.
_CACHE_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "build", "iosevka-charon"
)


# === Which Iosevka Charon font backs each Recursive Charon font ============

# Iosevka Charon ships two families:
#   * "IosevkaCharon"      -- quasi-proportional (backs Recursive Charon Sans)
#   * "IosevkaCharonMono"  -- monospace          (backs Recursive Charon Mono)
#
# The variable font spans both, so it is backed by the proportional family
# (its default MONO=0 location is the Sans/proportional design).
#
# Iosevka Charon ships Light / Regular / Medium / Bold plus italics. Recursive
# Charon has more weights than that; each Recursive weight is matched to the
# nearest Iosevka weight below. Because the borrowed glyphs are fallbacks for
# characters Recursive never drew, a close weight is more than good enough.

# Recursive OS/2 weight (usWeightClass) -> Iosevka Charon style stem.
_WEIGHT_TO_IOSEVKA = {
    300: "Light",
    400: "Regular",
    500: "Medium",
    600: "Bold",   # Iosevka has no SemiBold; Bold is the nearest heavier cut
    700: "Bold",
    800: "Bold",
    900: "Bold",
    1000: "Bold",
}


def _iosevka_style(weight, italic):
    """Build an Iosevka Charon style name, e.g. (700, True) -> 'BoldItalic'."""
    stem = _WEIGHT_TO_IOSEVKA.get(weight, "Regular")
    if italic:
        # Iosevka spells the upright-Regular italic simply "Italic".
        return "Italic" if stem == "Regular" else stem + "Italic"
    return stem


def _iosevka_filename(is_mono, weight, italic):
    """Return the Iosevka Charon TTF path for a given Recursive style."""
    family = "IosevkaCharonMono" if is_mono else "IosevkaCharon"
    subdir = "iosevkacharonmono" if is_mono else "iosevkacharon"
    style = _iosevka_style(weight, italic)
    return os.path.join(subdir, f"{family}-{style}.ttf")


# === Downloading / caching the Iosevka Charon release ======================

def ensure_iosevka_charon():
    """
    Download and extract the pinned Iosevka Charon release if not cached.

    Returns the directory containing the extracted `iosevkacharon/` and
    `iosevkacharonmono/` font folders.
    """
    version_dir = os.path.join(_CACHE_ROOT, IOSEVKA_CHARON_VERSION)
    marker = os.path.join(version_dir, ".complete")
    if os.path.exists(marker):
        return version_dir

    os.makedirs(version_dir, exist_ok=True)
    print(f"🏗  Downloading Iosevka Charon {IOSEVKA_CHARON_VERSION}")
    with urllib.request.urlopen(_RELEASE_URL) as resp:
        data = resp.read()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(version_dir)

    open(marker, "w").close()
    print(f"🏗  Extracted Iosevka Charon to {version_dir}")
    return version_dir


# === Glyph copying =========================================================

def _copy_glyph(name, src, dst, src_glyf, dst_glyf, src_hmtx, dst_hmtx,
                glyph_order):
    """
    Recursively copy glyph *name* (and any components it references) from the
    source font into the destination font. Existing destination glyphs are
    never overwritten -- Recursive Charon always wins.
    """
    if name in dst_glyf.glyphs:
        return

    glyph = src_glyf[name]

    # Copy components first so composite glyphs resolve.
    if glyph.isComposite():
        for component in glyph.components:
            _copy_glyph(component.glyphName, src, dst, src_glyf, dst_glyf,
                        src_hmtx, dst_hmtx, glyph_order)

    dst_glyf[name] = glyph
    dst_hmtx[name] = src_hmtx[name]
    glyph_order.append(name)


def _build_cmap(mapping):
    """
    Build a fresh `cmap` table from a {codepoint: glyphName} *mapping*.

    Emits a format-4 subtable (BMP only) and a format-12 subtable (full
    range), each on the Unicode (platform 0) and Windows (platform 3)
    platforms. This keeps BMP-only consumers working while exposing the
    supplementary-plane characters Iosevka Charon contributes.
    """
    bmp = {cp: g for cp, g in mapping.items() if cp <= 0xFFFF}

    cmap = newTable("cmap")
    cmap.tableVersion = 0

    def fmt4(platform_id, enc_id):
        sub = CmapSubtable.newSubtable(4)
        sub.platformID, sub.platEncID = platform_id, enc_id
        sub.format, sub.language = 4, 0
        sub.cmap = dict(bmp)
        return sub

    def fmt12(platform_id, enc_id):
        sub = CmapSubtable.newSubtable(12)
        sub.platformID, sub.platEncID = platform_id, enc_id
        sub.format, sub.reserved = 12, 0
        sub.length, sub.language, sub.nGroups = 0, 0, 0
        sub.cmap = dict(mapping)
        return sub

    # format-4 for the BMP on Unicode + Windows; format-12 for the full range.
    cmap.tables = [fmt4(0, 3), fmt4(3, 1), fmt12(0, 4), fmt12(3, 10)]
    return cmap


def merge_font(recursive_path, iosevka_path, out_path=None):
    """
    Fill gaps in the Recursive Charon font at *recursive_path* using glyphs
    from the Iosevka Charon font at *iosevka_path*.

    Only codepoints absent from Recursive Charon are borrowed. Returns the
    number of codepoints added.
    """
    if out_path is None:
        out_path = recursive_path

    dst = TTFont(recursive_path)
    src = TTFont(iosevka_path)

    if dst["head"].unitsPerEm != src["head"].unitsPerEm:
        raise ValueError(
            "unitsPerEm mismatch: Recursive Charon "
            f"{dst['head'].unitsPerEm} vs Iosevka Charon "
            f"{src['head'].unitsPerEm}; glyph copy would need scaling."
        )

    dst_cmap = dst.getBestCmap()
    src_cmap = src.getBestCmap()

    missing = {cp: gname for cp, gname in src_cmap.items()
               if cp not in dst_cmap}
    if not missing:
        return 0

    dst_glyf = dst["glyf"]
    src_glyf = src["glyf"]
    dst_hmtx = dst["hmtx"]
    src_hmtx = src["hmtx"]

    # Force any glyph-indexed variation tables to decompile against the
    # *current* glyph order before we grow it. gvar in particular asserts that
    # its stored glyphCount matches the glyph order at decompile time, so it
    # must be read now, not after setGlyphOrder() below.
    gvar = dst["gvar"] if "gvar" in dst else None
    if gvar is not None:
        gvar.ensureDecompiled()

    glyph_order = dst.getGlyphOrder()[:]

    for gname in missing.values():
        _copy_glyph(gname, src, dst, src_glyf, dst_glyf, src_hmtx, dst_hmtx,
                    glyph_order)

    dst.setGlyphOrder(glyph_order)

    # Give every borrowed glyph an (empty) gvar entry so gvar stays in sync
    # with the glyph order. The borrowed glyphs are static -- they don't
    # participate in the variation space -- which is exactly right for
    # fallback coverage glyphs.
    if gvar is not None:
        for gname in glyph_order:
            if gname not in gvar.variations:
                gvar.variations[gname] = []

    # Rebuild the cmap from the merged codepoint->glyph map. Recursive's cmap
    # has only format-4 (BMP) subtables, but Iosevka contributes thousands of
    # codepoints -- including 2500+ in the supplementary planes -- which need
    # a format-12 subtable. Rather than patch the existing subtables (which
    # would overflow format-4), synthesize a fresh, correct cmap: a format-4
    # for the BMP and a format-12 covering the full range, each published on
    # both the Unicode (0) and Windows (3) platforms.
    merged = dict(dst_cmap)
    merged.update(missing)
    dst["cmap"] = _build_cmap(merged)

    # maxp glyph count is derived from glyf on compile, but keep it honest.
    dst["maxp"].numGlyphs = len(glyph_order)

    dst.save(out_path)
    return len(missing)


# === Extending a whole build tree ==========================================

def _classify(font_path):
    """
    Inspect a built Recursive Charon font and return (is_mono, weight,
    italic) so the right Iosevka Charon donor can be chosen. Works for both
    the variable font (uses default weight) and the static instances.
    """
    font = TTFont(font_path)
    name = os.path.basename(font_path)

    # The variable font carries every axis; treat it as proportional (Sans)
    # at its default weight, matching its MONO=0 default location.
    if "fvar" in font:
        return (False, int(font["OS/2"].usWeightClass), False)

    is_mono = "Mono" in name or "Mn " in name
    italic = font["OS/2"].fsSelection & 0x01 == 1  # ITALIC bit
    weight = int(font["OS/2"].usWeightClass)
    return (is_mono, weight, italic)


# The build writes final fonts into these subdirectories of the output dir.
_OUTPUT_SUBDIRS = ("Variable_TTF", "Static_TTF")


def extend_build(fonts_dir):
    """
    Extend every Recursive Charon .ttf under *fonts_dir* with Iosevka Charon
    fallback glyphs.

    Only the Variable_TTF and Static_TTF output subdirectories are searched
    when they exist (the same directories the rest of the build treats as
    final output); otherwise *fonts_dir* is walked directly, which supports
    running this module standalone on a folder of fonts.

    Static .otf fonts are skipped: Iosevka Charon ships only TrueType, and
    matching TrueType instances are extended instead.
    """
    iosevka_dir = ensure_iosevka_charon()

    search_roots = [os.path.join(fonts_dir, d) for d in _OUTPUT_SUBDIRS
                    if os.path.isdir(os.path.join(fonts_dir, d))]
    if not search_roots:
        search_roots = [fonts_dir]

    ttfs = []
    for root_dir in search_roots:
        for root, _dirs, files in os.walk(root_dir):
            # Don't descend into the WOFF2 output; those are re-generated
            # from the extended TTFs afterwards.
            _dirs[:] = [d for d in _dirs if d != "WOFF2"]
            for f in files:
                if f.lower().endswith(".ttf"):
                    ttfs.append(os.path.join(root, f))

    if not ttfs:
        print(f"⚠️  No .ttf fonts found under {fonts_dir} to extend")
        return

    print(f"🏗  Extending {len(ttfs)} font(s) with Iosevka Charon "
          f"{IOSEVKA_CHARON_VERSION}")
    for ttf in sorted(ttfs):
        is_mono, weight, italic = _classify(ttf)
        donor = os.path.join(iosevka_dir,
                             _iosevka_filename(is_mono, weight, italic))
        if not os.path.exists(donor):
            print(f"  ⚠️  No Iosevka donor {os.path.basename(donor)} for "
                  f"{os.path.basename(ttf)}; skipping")
            continue
        added = merge_font(ttf, donor)
        print(f"  ✅ {os.path.basename(ttf)}: +{added} codepoints "
              f"from {os.path.basename(donor)}")

    print("✅ Extended fonts with Iosevka Charon coverage")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extend Recursive Charon fonts with Iosevka Charon "
                    "glyph coverage.")
    parser.add_argument("fonts_dir",
                        help="Directory tree of built Recursive Charon fonts")
    args = parser.parse_args()
    extend_build(args.fonts_dir)
