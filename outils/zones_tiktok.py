"""Textes et visages sous l'interface TikTok : onglets en haut, boutons à droite, légende et pseudo en bas.
Usage : zones_tiktok.py <video> [fps=2]  -> textes et visages hors zone sûre, code 1 s'il y en a.
Visages : seulement ceux d'au moins 4 % de la hauteur (la figure, pas la foule) ; même zone que les textes.
Zone sûre (fractions de l'image 9:16) : x 0,06-0,83 ; y 0,12-0,75. Colonne de boutons à droite
de 0,34 à 0,86 de haut ; au-dessus et au-dessous, la marge droite redescend à 0,94.
"""
import json, os, subprocess, sys, tempfile

HAUT, BAS, GAUCHE, DROITE, DROITE_LIBRE = 0.12, 0.75, 0.06, 0.83, 0.94
BOUTONS = (0.34, 0.86)
ICI = os.path.dirname(os.path.abspath(__file__))


def hors_zone(x, y, w, h):
    """Raisons pour lesquelles une boîte de texte touche l'interface (liste vide = OK)."""
    r = []
    if y < HAUT: r.append("haut (onglets)")
    if y + h > BAS: r.append("bas (légende)")
    if x < GAUCHE: r.append("bord gauche")
    droite = DROITE if y + h > BOUTONS[0] and y < BOUTONS[1] else DROITE_LIBRE
    if x + w > droite: r.append("droite (boutons)")
    return r


def main(video, fps=2):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale=1080:-2", f"{d}/%04d.jpg"], check=True)
        subprocess.run([f"{ICI}/texts", d], check=True, capture_output=True)
        subprocess.run([f"{ICI}/faces", d], check=True, capture_output=True)
        textes = json.load(open(f"{d}/texts.json")); visages = json.load(open(f"{d}/faces.json"))
    fautes = []
    for f, boites in sorted(textes.items()):
        t = (int(f.split(".")[0]) - 1) / fps
        for x, y, w, h, s in boites:
            if r := hors_zone(x, y, w, h):
                fautes.append(f"{t:5.1f}s « {s} » : {', '.join(r)}")
    print("\n".join(fautes) or "textes : tous dans la zone sûre TikTok")
    tetes = []
    for f, boites in sorted(visages.items()):
        t = (int(f.split(".")[0]) - 1) / fps
        for x, y, w, h in boites:
            if h >= 0.04 and (r := hors_zone(x, y, w, h)):
                tetes.append(f"{t:5.1f}s visage ({x:.2f}, {y:.2f}, {w:.2f}×{h:.2f}) : {', '.join(r)}")
    print("\n".join(tetes) or "visages : tous hors de l'interface TikTok")
    return 1 if fautes or tetes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], *map(float, sys.argv[2:])))
