# Frappes retenues d'Experience : un temps = 1/4 de mesure entre deux temps forts mesurés (attaques de basse les plus fortes,
# mesure ≈ 2,596 s, 92,4 BPM) ; la frappe d'un temps = l'attaque RÉELLE la plus précoce parmi les fortes (≥ 75 % de la plus
# forte) dans ±80 ms (basse 30-200 Hz ou piano 200-4000 Hz, attaques.json). Drop = temps fort 121,49 s (arrivée du pic « les plus revus » YouTube 120-123 s, attaque de basse la plus forte du passage).
# usage : grille.py DROP_timeline [drop_morceau≈121.49]  -> frappes.json (temps morceau + timeline, MOFF = drop_morceau - DROP_timeline)
import json, sys
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/G6/rythme/"
A = json.load(open(D + "attaques.json")); att = A["basse"] + A["piano"]
BARS = [103.329, 105.931, 108.491, 111.14, 113.736, 116.338, 118.884, 121.492, 124.105, 126.68, 129.275, 131.867, 134.501]
DROPT = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
F = []
for b0, b1 in zip(BARS, BARS[1:]):
    for q in range(4):
        g = b0 + (b1 - b0) * q / 4
        c = [a for a in att if abs(a[0] - g) <= 0.08]
        if not c: continue
        mx = max(a[1] for a in c)
        F.append(round(min(a[0] for a in c if a[1] >= 0.75 * mx), 3))
F = sorted(set(F))
DROPM = float(sys.argv[2]) if len(sys.argv) > 2 else 121.49
drop = min(F, key=lambda x: abs(x - DROPM))
MOFF = round(drop - DROPT, 3)
res = {"MOFF": MOFF, "drop_morceau": drop, "frappes_morceau": F,
       "frappes_timeline": [round(f - MOFF, 3) for f in F if -0.01 <= f - MOFF <= 16]}
json.dump(res, open(D + "frappes.json", "w"), indent=1)
print("drop", drop, "MOFF", MOFF); print(res["frappes_timeline"])
