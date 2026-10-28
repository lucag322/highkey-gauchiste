// Luca shares a TikTok / Reel / Short in one of the SALONS (with or without a word):
// #inspi adds it to his taste library (skill `gouts`), #inspigauchiste turns it into a
// style recipe for the account's edits (skill `inspi-gauchiste`). The bot answers in the channel.
// The bot downloads and measures the video itself (yt-dlp, ffmpeg); the headless Claude
// (Sonnet) only reads the results and writes in its vault folder: it gets no shell at all.
import { execFile, spawn } from 'node:child_process';
import { mkdir, readdir, rename, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';

const run = promisify(execFile);
const VAULT = join(homedir(), 'Documents/Cerveau');
// Channel name without dashes or case (Discord shows "InspiGauchiste" as "inspigauchiste").
const SALONS = {
  inspi: { skill: 'gouts', dossier: 'Projets/bibliotheque-artistique', images: 'images', titre: 'Vidéo reçue' },
  inspigauchiste: { skill: 'inspi-gauchiste', dossier: 'Projets/highkey-gauchiste', images: 'inspis/images', titre: 'Edit reçu' },
};
const TMP = join(homedir(), 'Movies/Goûts _tmp');
const DELAI = 15 * 60_000;
const LIEN = /https:\/\/([\w-]+\.)*(tiktok\.com|instagram\.com|youtube\.com|youtu\.be)\/\S+/g;
const outils = (dossier) => ['Read', 'Glob', 'Grep', `Edit(~/Documents/Cerveau/${dossier}/**)`, `Write(~/Documents/Cerveau/${dossier}/**)`];

// One video at a time: two analyses would edit the same synthesis / index file.
let file = Promise.resolve();

const slugifier = (s) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30) || 'video';

// Instagram often needs a logged-in session: retry with Chrome's cookies.
async function ytdlp(args, opts) {
  try {
    return await run('yt-dlp', args, opts);
  } catch {
    return run('yt-dlp', ['--cookies-from-browser', 'chrome', ...args], opts);
  }
}

// Steps 1, 2 and the stills of the skill, done here so Claude needs no shell.
// imagesVault: folder of the stills, relative to the vault.
export async function preparer(lien, W, imagesVault) {
  const date = new Date().toISOString().slice(0, 10);
  await mkdir(W, { recursive: true });

  const { stdout } = await ytdlp(['-J', '--no-playlist', lien], { maxBuffer: 64 * 2 ** 20, timeout: 120_000 });
  const m = JSON.parse(stdout);
  const meta = {
    url: lien, titre: m.title, createur: m.uploader || m.channel || m.uploader_id, description: m.description,
    duree: m.duration, musique: [m.track, m.artist].filter(Boolean).join(' — ') || null, tags: m.tags,
  };
  await writeFile(join(W, 'meta.json'), JSON.stringify(meta, null, 2));
  await ytdlp(['--no-playlist', '-f', 'bv*[height<=1080]+ba/b', '-o', join(W, 'video.%(ext)s'), lien], { timeout: 300_000 });
  const video = join(W, (await readdir(W)).find((f) => f.startsWith('video.')));

  const sonde = JSON.parse((await run('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'format=duration:stream=width,height', '-of', 'json', video])).stdout);
  const duree = Number(sonde.format.duration);
  const scenes = await run('ffmpeg', ['-v', 'info', '-i', video, '-vf', "select='gt(scene,0.3)',showinfo", '-f', 'null', '-'],
    { maxBuffer: 64 * 2 ** 20, timeout: 300_000 });
  const coupes = [...scenes.stderr.matchAll(/pts_time:([\d.]+)/g)].map(([, t]) => Number(Number(t).toFixed(2)));
  await run('ffmpeg', ['-v', 'error', '-y', '-i', video, '-vf', 'fps=1,scale=320:-1,tile=4x4', join(W, 'planche-%02d.jpg')],
    { timeout: 300_000 });

  const slug = `${date}-${slugifier(meta.createur || 'video')}`;
  const images = join(VAULT, imagesVault, slug);
  await mkdir(images, { recursive: true });
  const stills = [];
  for (let i = 0; i < 6; i++) {
    const t = Number(((duree * (i + 0.5)) / 6).toFixed(1));
    await run('ffmpeg', ['-v', 'error', '-y', '-ss', `${t}`, '-i', video, '-frames:v', '1', '-vf', 'scale=480:-1',
      '-q:v', '4', join(images, `t${t}.jpg`)]);
    stills.push(`${imagesVault}/${slug}/t${t}.jpg`);
  }
  const mesures = {
    slug, duree: Number(duree.toFixed(1)), largeur: sonde.streams[0].width, hauteur: sonde.streams[0].height,
    coupes, coupes_par_10s: Number(((coupes.length * 10) / duree).toFixed(1)), stills,
    planches: (await readdir(W)).filter((f) => f.startsWith('planche-')).map((f) => join(W, f)),
  };
  await writeFile(join(W, 'mesures.json'), JSON.stringify(mesures, null, 2));
}

function analyser(W, note, salon) {
  const prompt = [
    `Lis ${join(homedir(), '.claude/skills', salon.skill, 'SKILL.md')} et applique-le (mode Discord) à la vidéo déjà préparée dans ${W}.`,
    `Note de Luca : ${note ? `« ${note} »` : 'aucune'}`,
    'Ta réponse finale part telle quelle sur Discord : seulement le message du modèle, rien avant ni après.',
  ].join('\n');
  return new Promise((resolve, reject) => {
    const claude = spawn('claude', [
      '-p', prompt, '--model', 'sonnet', '--no-session-persistence',
      '--permission-mode', 'dontAsk', '--allowedTools', ...outils(salon.dossier),
    ], { cwd: VAULT, env: { ...process.env, CERVEAU_HOOK: '1' }, stdio: ['ignore', 'pipe', 'pipe'] }); // CERVEAU_HOOK: no session summary
    let sortie = '';
    let erreurs = '';
    claude.stdout.on('data', (d) => { sortie += d; });
    claude.stderr.on('data', (d) => { erreurs += d; });
    const minuteur = setTimeout(() => claude.kill(), DELAI);
    claude.on('close', (code) => {
      clearTimeout(minuteur);
      if (code === 0 && sortie.trim()) return resolve(sortie.trim());
      console.error(`[inspi] code ${code}\nstdout: ${sortie}\nstderr: ${erreurs}`);
      const raison = (erreurs || sortie).trim().split('\n').pop()?.slice(0, 150) || 'aucune sortie';
      reject(new Error(`claude a quitté (${code}) : ${raison}`));
    });
  });
}

async function traiter(lien, note, salon) {
  const W = join(TMP, `${Date.now()}`);
  try {
    try {
      await preparer(lien, W, `${salon.dossier}/${salon.images}`);
    } catch (e) {
      console.error('[inspi]', e);
      throw new Error('vidéo pas récupérée (privée, supprimée ou bloquée)');
    }
    return await analyser(W, note, salon);
  } finally {
    await rename(W, join(homedir(), '.Trash', `goûts-${Date.now()}`)).catch(() => {});
  }
}

export async function onMessage(message) {
  const salon = SALONS[message.channel.name?.toLowerCase().replace(/[^a-z0-9]/g, '')];
  if (!salon) return;
  const liens = message.content.match(LIEN);
  if (!liens) return;
  const note = message.content.replace(LIEN, '').trim();
  for (const lien of liens) {
    const attente = await message.reply(`## 🎨 ${salon.titre}\nAnalyse en cours, 2 à 5 min.`);
    file = file.then(() => traiter(lien, note, salon)
      .then((texte) => attente.edit(texte.slice(0, 1900)))
      .catch((e) => attente.edit(`## ❌ Analyse ratée\n${e.message.slice(0, 200)}\n-# Réessaie, ou donne le lien dans Claude.`)));
  }
}
