"""Builds the background image used by interactive_map.html.

BACKGROUND INVESTIGATION NOTES (user asked whether a more accurate/game-like
background map exists in these resources):

The live in-game "World Map" screen the user screenshotted is NOT a single 2D
painted texture. It's a fully 3D scene assembled at runtime from ~30 separate
per-region terrain/prop asset bundles found in this folder (mapcoastdorne,
mapmountainnorth, mapcoastcrownlands, mapsopcrownlands, mapkingslanding,
mapcasterlyrock, maptunnelcrossing, mapdeco, mapterrainwater, maplighting,
etc.) - hundreds of individual 3D meshes/props lit and camera-angled at
runtime. There is no single baked "world map image" asset anywhere in this
dump (confirmed: searched worldmap.unity3d / worldmapv2.unity3d - UI Canvas
scene + a couple of small VFX/normal textures only; searched sagamap*.unity3d,
generatedsprite_mapui_*.unity3d - unrelated UI chrome/icons). So a pixel-exact
reproduction of the reference screenshot's painted look isn't extractable
without fully reconstructing that 3D scene (out of scope here).

The closest static asset is Westeros_Alpha_6_WorldMap_DiffuseAndSmoothness_
Bitmap - confirmed (by direct visual inspection) to be a flat, blotchy
biome-tinted top-down texture (solid orange/green/brown regions + thin white
road/river lines), i.e. exactly the kind of low-detail "reference/LOD/debug"
texture the user suspected - not the detailed painted terrain seen in-game.
It DOES align pixel-perfectly with the POI coordinate space though (verified
by overlaying all 7,694 nodes on it in the previous pass), so it's kept as
the base layer for correctness, and enhanced here with a coastline/relief
shading pass built from the WorldMap_NormalsAndShadow_Bitmap's alpha channel
(the only channel that carries data - it's a coastline/steep-edge shadow
mask) to make coasts and mountain ridgelines read more clearly, softening the
"flat color blob" look. This is a modest cosmetic improvement, not a claim of
matching the live 3D render.
"""
import math
import os
import texture2ddecoder
from PIL import Image, ImageEnhance, ImageOps, ImageChops, ImageFilter

BASE = os.path.dirname(__file__)
EXT = os.path.join(BASE, '_extracted')


def soften_warm_band(rgb_img, center_deg=33, half_width_deg=22, desat_strength=0.42, value_lift=0.05):
    """Selectively softens the saturated yellow/orange hue band that dominates the
    southern half of the map (Westerlands/Vale/Crownlands/Reach/Stormlands/Dorne all
    share this same tan-orange tint - see module docstring). User feedback: this
    color was "rough on the eyes" and, separately, clashed with the Crossing POI
    marker color on the interactive map (fixed on that side too, in
    _build_interactive_map.py, by darkening that marker's color).

    Only desaturates/lightens within a hue band centered on that yellow-orange
    (~33 degrees), using a smooth raised-cosine falloff rather than a hard cutoff,
    so there's no visible ring/boundary artifact where the effect starts or stops.
    Verified against sample pixels: the most strongly-hit "yellow" tone (hue ~37,
    e.g. RGB 231,163,54) gets knocked down to ~61% of its original saturation,
    the more orange-red tone further from band center (hue ~21, e.g. RGB
    228,110,48) only ~83% (a much gentler touch), the North's brownish tone
    (hue ~17) is barely touched (~92%), and greens (hue ~81, Riverlands/forest)
    are completely untouched (outside the band entirely).
    """
    hsv = rgb_img.convert('HSV')
    h, s, v = hsv.split()

    def _weight(h_255):
        deg = h_255 * 360.0 / 255.0
        d = abs(deg - center_deg)
        if d > half_width_deg:
            return 0.0
        return 0.5 * (1 + math.cos(math.pi * d / half_width_deg))

    sat_lut = h.point(lambda hv: int(round((1 - _weight(hv) * desat_strength) * 255)))
    val_lut = h.point(lambda hv: int(round(_weight(hv) * value_lift * 255)))

    s2 = ImageChops.multiply(s, sat_lut)   # s * sat_lut/255 -> desaturate within band
    v2 = ImageChops.screen(v, val_lut)     # nudge lighter within band (softer look)

    return Image.merge('HSV', (h, s2, v2)).convert('RGB')


def decode_astc_rgba(path):
    with open(path, 'rb') as f:
        data = f.read()
    header = data[:16]
    bx, by = header[4], header[5]
    xsize = header[7] | (header[8] << 8) | (header[9] << 16)
    ysize = header[10] | (header[11] << 8) | (header[12] << 16)
    payload = data[16:]
    rgba = texture2ddecoder.decode_astc(payload, xsize, ysize, bx, by)
    return Image.frombytes('RGBA', (xsize, ysize), rgba, 'raw', 'BGRA')


def main():
    diffuse_path = os.path.join(BASE, 'Westeros_Alpha_6_WorldMap_DiffuseAndSmoothness_Bitmap.1785525681.astc')
    shadow_path = os.path.join(BASE, 'Westeros_Alpha_6_WorldMap_NormalsAndShadow_Bitmap.1785525681.astc')

    diffuse = decode_astc_rgba(diffuse_path).convert('RGB')
    diffuse = ImageEnhance.Brightness(diffuse).enhance(3.2)
    diffuse = ImageOps.autocontrast(diffuse, cutoff=1)
    diffuse = soften_warm_band(diffuse)

    shadow_alpha = decode_astc_rgba(shadow_path).getchannel('A')  # 255=flat interior, 0=coast/steep edge
    shadow_soft = shadow_alpha.filter(ImageFilter.GaussianBlur(1.2))
    # keep interior at full brightness; only darken down to ~55% at the strongest edges
    shadow_remapped = shadow_soft.point(lambda v: int(140 + (v / 255) * 115))
    shade_rgb = Image.merge('RGB', (shadow_remapped, shadow_remapped, shadow_remapped))

    final = ImageChops.multiply(diffuse, shade_rgb)

    # Vertical flip: the raw texture/node coordinate space stores row 0 at the BOTTOM
    # (confirmed via the 11 Great House Capitals - sorting by raw node y put Sunspear/
    # Dorne, true south, at the lowest y, and Winterfell, true north, at the highest y,
    # the exact opposite of a north-up screen). Flipping here makes the saved JPEG
    # itself north-up, matching the node y-flip applied at draw time in
    # _build_interactive_map.py (cy = BG_H - d.y), so the two stay visually consistent.
    final = final.transpose(Image.FLIP_TOP_BOTTOM)

    out_path = os.path.join(EXT, 'worldmap_background.jpg')
    final.save(out_path, quality=88)
    print('wrote', out_path, final.size, round(os.path.getsize(out_path) / 1024, 1), 'KB')


if __name__ == '__main__':
    main()
