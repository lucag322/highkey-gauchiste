---
date: 2026-10-26
source: https://vm.tiktok.com/ZN8DVExnU/
createur: "@editsofourtimes"
style: nouveau
son: Txmy - Solace
---
# editsofourtimes - Obama karaoké discours
↑ [[Projets/highkey-gauchiste/inspis|inspis]]
- Note de Luca : aucune, hypothèse — retenir la structure karaoké + B-roll + fin document d'époque
- Ce que ça montre : discours fragmenté mot à mot en sous-titres + plans de foule qui illustrent chaque concept, finit sur un document d'archive (CNN Breaking News)
## À recopier
- Karaoké discours : chaque fragment de la phrase = un plan différent (B-roll meetings, manifs, foule)
- Sous-titres jaune ~#FFD700, italic, sans-serif léger, bas-centre, texte nu sans fond
- Plan long d'ouverture (5-6 s) pour asseoir le sujet, puis rafale de coupes courtes
- Rafale ultra-rapide vers la fin (5 coupes en 1,5 s) sur un moment fort
- Fin "document d'époque" : capture JT ou breaking news plein écran, renforce la gravité
- Musique atmosphérique sous la voix, voix audible tout du long
## Recette avec nos outils
- `words.py` pour sous-titres jaune italic mot à mot (sans guillemets, voir conflits)
- B-roll LFI : meetings, manifs, Assemblée — 1 plan par fragment de discours
- `cards.py` pour la fin : capture JT ou une de journal sur noir
- Rafale de coupes sèches sur le moment fort (pas de transition)
- Recadrer chaque plan en 9:16 sur le visage ou l'action — `framing.py`
- Musique : chercher équivalent de Txmy - Solace (piano ambient, pas de drop fort)
## Mesures
- 4:3 non vertical, 21,7 s, 6,9 coupes / 10 s, coupes sur la parole (pas sur le beat)
- Couleurs : #1A1414 #1D3B6E #C0202A #D4A882 #FFD700
## À ne pas recopier
- Guillemets à l'écran autour des sous-titres (règle Luca)
- Durée 21,7 s > 20 s
- Format 960×720 non vertical (recadrer en 9:16 obligatoire)
![[Projets/highkey-gauchiste/inspis/images/2026-10-26-editsofourtimes/t1.8.jpg|240]] ![[Projets/highkey-gauchiste/inspis/images/2026-10-26-editsofourtimes/t9.jpg|240]]
