// TikTok account: a video dropped in ~/Movies/highkey-gauchiste/a-publier/ with a
// same-name .json ({"legende": "...", "hashtags": ["#lfi"]}) is proposed in the tiktok
// channel with Valider / Refuser buttons. Valider uploads it to the TikTok drafts
// (src/tiktok.js); Luca adds the trending sound, pastes the caption and posts in the app.
// Files move to proposees/, envoyees/ or refusees/: the folder is the state.
// A sent video keeps a <name>.suivi.json in envoyees/ until TikTok delivers the draft
// (often 15-45 min); each pass checks it and updates the Discord message. Once delivered,
// the video and the paths listed in its .json "apres_envoi" (HD, working files) are deleted.
// A video refused for a TikTok limit (5 pending drafts / 24 h, requests per minute) waits in
// proposees/<name>.attente.json and is sent again automatically, one per pass. A limit pauses
// the whole queue; when it reopens, the next video is the one least like the last ones sent
// (style = letter of the id, then figure), so the 5 daily drafts are not all the same style.
// Buttons carry the file name, so they keep working after a bot restart
// (demanderValidation waits in one process and gives up after a delay).
import { execFile } from 'node:child_process';
import { mkdir, readdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { join, parse, resolve } from 'node:path';
import { promisify } from 'node:util';
import { ActionRowBuilder, ButtonBuilder, ButtonStyle, escapeMarkdown, SlashCommandBuilder } from 'discord.js';
import { config } from '../src/secrets.js';
import { ARRIVE, connecte, dateParis, envoyerBrouillon, silence, statutBrouillon, toursAConfirmer } from '../src/tiktok.js';

const run = promisify(execFile);
const DOSSIER = process.env.TIKTOK_DOSSIER ?? join(homedir(), 'Movies/highkey-gauchiste/a-publier');
const VIDEO = /\.(mp4|mov|webm)$/i;
const STABLE = 60_000; // untouched for 1 min = export finished
const VERIFICATION = 2 * 60_000;
const APERCU = 9 * 2 ** 20; // Discord caps bot uploads at 10 MB
const STATUT = /\n\n(⏳|❌|✅|🗑️) [\s\S]*$/;
const SUIVI = 3 * 3_600_000; // a draft still missing after 3 h is reported and no longer checked
const ENVOYEES = join(DOSSIER, 'envoyees');
const PROPOSEES = join(DOSSIER, 'proposees');
const PROJET = join(DOSSIER, '..'); // apres_envoi paths are relative to it, and must stay inside it
const LIMITES = { spam_risk_too_many_pending_share: 30 * 60_000, rate_limit_exceeded: 60_000 }; // wait before retrying
const attente = (nom) => join(PROPOSEES, `${nom}.attente.json`);

// One TikTok job at a time: proposals and uploads share the API rate limits.
let file = Promise.resolve();
const echecs = new Set(); // proposals that failed, not retried until restart

const salon = (client) => client.channels.fetch(config.channels.tiktok ?? config.channels.general);

export const boutons = (nom) => new ActionRowBuilder().addComponents(
  new ButtonBuilder().setCustomId(`tiktok:valider:${nom}`).setLabel('Valider').setEmoji('✅').setStyle(ButtonStyle.Success),
  new ButtonBuilder().setCustomId(`tiktok:refuser:${nom}`).setLabel('Refuser').setEmoji('❌').setStyle(ButtonStyle.Danger),
);

const lireMeta = async (dossier, nom) => JSON.parse(await readFile(join(dossier, `${nom}.json`), 'utf8'));
export const legende = (meta) => [meta.legende, [meta.hashtags ?? []].flat().join(' ')].filter(Boolean).join('\n');

export const texteProposition = (nom, meta) => [
  '## 🎬 TikTok à valider',
  `**${escapeMarkdown(nom)}**`,
  '',
  escapeMarkdown(legende(meta)) || '_Pas de légende_',
  '-# Valider = envoi en brouillon TikTok',
].join('\n');

async function trouverVideo(dossier, nom) {
  const fichier = (await readdir(dossier)).find((f) => VIDEO.test(f) && parse(f).name === nom);
  if (!fichier) throw new Error(`vidéo ${nom} introuvable dans ${dossier.split('/').slice(-2).join('/')}`);
  return join(dossier, fichier);
}

async function deplacer(nom, de, vers) {
  await mkdir(join(DOSSIER, vers), { recursive: true });
  for (const f of await readdir(join(DOSSIER, de))) {
    if (parse(f).name === nom) await rename(join(DOSSIER, de, f), join(DOSSIER, vers, f));
  }
}

// Videos with their .json, both untouched for STABLE ms.
async function pretes() {
  await mkdir(DOSSIER, { recursive: true });
  const fichiers = await readdir(DOSSIER);
  const noms = [];
  for (const f of fichiers.filter((f) => VIDEO.test(f))) {
    const { name } = parse(f);
    if (!fichiers.includes(`${name}.json`) || echecs.has(name)) continue;
    const dates = await Promise.all([f, `${name}.json`].map(async (x) => (await stat(join(DOSSIER, x))).mtimeMs));
    if (Date.now() - Math.max(...dates) > STABLE) noms.push(name);
  }
  return noms;
}

// Small H.264 copy so the phone can play it inside Discord.
async function apercu(video) {
  const sortie = join(tmpdir(), `tiktok-apercu-${Date.now()}.mp4`);
  await run('ffmpeg', ['-v', 'error', '-y', '-i', video, '-vf', "scale='min(540,iw)':-2", '-c:v', 'libx264', '-preset', 'veryfast',
    '-crf', '30', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-fs', `${APERCU}`, sortie], { timeout: 300_000 });
  return sortie;
}

export async function proposer(client, nom) {
  const canal = await salon(client);
  try {
    if (`tiktok:valider:${nom}`.length > 100) throw new Error('nom trop long (85 caractères max)');
    const meta = await lireMeta(DOSSIER, nom);
    const chemin = await apercu(await trouverVideo(DOSSIER, nom));
    try {
      await canal.send({ content: texteProposition(nom, meta), components: [boutons(nom)], files: [{ attachment: chemin, name: 'apercu.mp4' }] });
    } finally {
      await rm(chemin, { force: true });
    }
    await deplacer(nom, '.', 'proposees');
  } catch (e) {
    console.error('[tiktok]', e);
    echecs.add(nom);
    await canal.send(`## ❌ TikTok non proposé\n**${escapeMarkdown(nom)}**\n${e.message.slice(0, 200)}\n-# Corrige le fichier puis relance le bot.`);
  }
}

// One status check per sent draft, then the Discord message says where it is.
export async function suivre(client) {
  for (const f of (await readdir(ENVOYEES).catch(() => [])).filter((f) => f.endsWith('.suivi.json'))) {
    const suivi = JSON.parse(await readFile(join(ENVOYEES, f), 'utf8'));
    let fin;
    try {
      const { status, fail_reason } = await statutBrouillon(suivi.publishId);
      if (ARRIVE.includes(status)) fin = '✅ Dans tes brouillons TikTok\n-# Ouvre la notif TikTok, ajoute le son, colle la légende ci-dessous.';
      else if (status === 'FAILED') fin = `❌ TikTok a rejeté la vidéo : ${fail_reason ?? 'raison inconnue'}`;
    } catch (e) {
      console.error('[tiktok]', e); // network or token: checked again next pass
    }
    if (!fin && Date.now() - suivi.depuis > SUIVI) fin = '❌ Pas arrivée après 3 h\n-# Regarde la boîte de réception TikTok.';
    if (!fin) continue;
    if (fin.startsWith('✅')) await nettoyer(f.slice(0, -'.suivi.json'.length));
    try {
      const message = await (await client.channels.fetch(suivi.salon)).messages.fetch(suivi.message);
      await message.edit({ content: `${message.content.replace(STATUT, '')}\n\n${fin}` });
    } catch (e) {
      console.error('[tiktok]', e); // message deleted: nothing left to update
    }
    await rm(join(ENVOYEES, f));
  }
}

// Draft delivered: TikTok has the video, so the local copies only take space.
async function nettoyer(nom) {
  const meta = await lireMeta(ENVOYEES, nom).catch(() => ({}));
  for (const f of await readdir(ENVOYEES)) {
    if (VIDEO.test(f) && parse(f).name === nom) await rm(join(ENVOYEES, f));
  }
  for (const chemin of meta.apres_envoi ?? []) {
    const cible = resolve(PROJET, chemin);
    if (cible.startsWith(`${resolve(PROJET)}/`)) await rm(cible, { recursive: true, force: true });
    else console.error('[tiktok] apres_envoi hors du projet ignoré :', chemin);
  }
}

// "melenchon-A6" -> style "A" (L1, the lot 1 aura, counts as A), figure "melenchon".
const style = (nom) => { const lettre = nom.split('-').pop()[0]; return lettre === 'L' ? 'A' : lettre; };
const figure = (nom) => nom.split('-').slice(0, -1).join('-');

// The video least like the recent sends: same style counts double, same figure once; ties keep order.
export function choisir(candidats, recents) {
  const score = (nom) => recents.reduce((s, r) => s + 2 * (style(r) === style(nom)) + (figure(r) === figure(nom)), 0);
  return candidats.reduce((meilleur, nom) => (score(nom) < score(meilleur) ? nom : meilleur));
}

// Last 4 sent videos, most recent first ("envoyee" written by valider, file date for older ones).
async function recents() {
  const noms = (await readdir(ENVOYEES).catch(() => []))
    .filter((f) => f.endsWith('.json') && f.split('.').length === 2).map((f) => f.slice(0, -'.json'.length));
  const dates = await Promise.all(noms.map(async (nom) => (await lireMeta(ENVOYEES, nom).catch(() => ({}))).envoyee
    ?? (await stat(join(ENVOYEES, `${nom}.json`))).mtimeMs));
  return noms.map((nom, i) => [nom, dates[i]]).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([nom]) => nom);
}

const enAttente = async () => (await readdir(PROPOSEES).catch(() => []))
  .filter((f) => f.endsWith('.attente.json')).map((f) => f.slice(0, -'.attente.json'.length));

// A TikTok limit is per account: the whole queue waits, not only the video that hit it.
async function pauser(pause) {
  for (const nom of await enAttente()) {
    const a = JSON.parse(await readFile(attente(nom), 'utf8'));
    await writeFile(attente(nom), JSON.stringify({ ...a, prochain: Math.max(a.prochain, Date.now() + pause) }));
  }
}

// Queued videos whose wait is over: one upload per pass, so the per-minute limit is never hit.
export async function relancer(client) {
  const prets = [];
  for (const nom of await enAttente()) {
    if (JSON.parse(await readFile(attente(nom), 'utf8')).prochain <= Date.now()) prets.push(nom);
  }
  if (!prets.length) return;
  const nom = choisir(prets, await recents());
  const { salon: idSalon, message: idMessage } = JSON.parse(await readFile(attente(nom), 'utf8'));
  let message;
  try {
    message = await (await client.channels.fetch(idSalon)).messages.fetch(idMessage);
  } catch (e) {
    console.error('[tiktok]', e); // message deleted: the video stays in proposees, no more retries
    await rm(attente(nom));
    return;
  }
  await valider(message, nom);
}

const verifier = (client) => {
  file = file.then(async () => {
    await suivre(client);
    await relancer(client);
    for (const nom of await pretes()) await proposer(client, nom);
  }).catch((e) => console.error('[tiktok]', e));
  return file;
};

export function onReady(client) {
  verifier(client);
  setInterval(() => verifier(client), VERIFICATION);
}

async function valider(message, nom) {
  const base = message.content.replace(STATUT, '');
  try {
    const dossier = join(DOSSIER, 'proposees');
    const id = await envoyerBrouillon(await trouverVideo(dossier, nom));
    const meta = await lireMeta(dossier, nom);
    await writeFile(join(dossier, `${nom}.json`), JSON.stringify({ ...meta, envoyee: Date.now() })); // order for recents()
    await rm(attente(nom), { force: true });
    await deplacer(nom, 'proposees', 'envoyees');
    await writeFile(join(ENVOYEES, `${nom}.suivi.json`),
      JSON.stringify({ publishId: id, salon: message.channelId, message: message.id, depuis: Date.now() }));
    await message.edit({ content: `${base}\n\n⏳ Envoyée, TikTok la traite (15 à 45 min)\n-# Ce message change quand le brouillon arrive.`, components: [] });
    if (legende(meta)) await message.channel.send(legende(meta)); // alone, so a long press copies it whole
  } catch (e) {
    console.error('[tiktok]', e);
    const pause = LIMITES[e.code];
    if (pause) {
      await writeFile(attente(nom), JSON.stringify({ salon: message.channelId, message: message.id, prochain: Date.now() + pause }));
      await pauser(pause);
      await message.edit({ content: `${base}\n\n⏳ En file d'attente : ${e.message}\n-# Envoi automatique dès que TikTok a une place.`, components: [] });
      return;
    }
    await message.edit({ content: `${base}\n\n❌ ${e.message.slice(0, 300)}`, components: [boutons(nom)] });
  }
}

export async function onButton(interaction) {
  const [prefixe, action, ...reste] = interaction.customId.split(':');
  if (prefixe !== 'tiktok') return;
  const nom = reste.join(':');
  const base = interaction.message.content.replace(STATUT, '');
  if (action === 'refuser') {
    await deplacer(nom, 'proposees', 'refusees');
    return interaction.update({ content: `${base}\n\n🗑️ Refusée`, components: [] });
  }
  // Buttons removed while sending: no double upload on a second tap.
  await interaction.update({ content: `${base}\n\n⏳ Envoi vers TikTok…`, components: [] });
  file = file.then(() => valider(interaction.message, nom));
  return file;
}

export const commands = [new SlashCommandBuilder().setName('tiktok').setDescription('État des envois TikTok')];

export async function handle(interaction) {
  await interaction.deferReply();
  await verifier(interaction.client);
  const compter = async (sous) => (await readdir(join(DOSSIER, sous)).catch(() => [])).filter((f) => VIDEO.test(f)).length;
  const tour = silence();
  const aConfirmer = toursAConfirmer();
  await interaction.editReply([
    '## 🎬 TikTok',
    connecte() ? '**Connecté**' : '**Pas connecté**',
    '',
    `- À valider : ${await compter('proposees')}`,
    `- Envoyées : ${await compter('envoyees')}`,
    `- Silence électoral : ${tour ? `jusqu'au ${dateParis(tour.fin)}` : 'non'}`,
    connecte() ? null : '-# Lance `npm run tiktok-connexion` sur le Mac.',
    aConfirmer.length ? `-# Dates à confirmer : ${aConfirmer.length} tour(s), voir elections.json` : null,
  ].filter((l) => l !== null).join('\n'));
}
