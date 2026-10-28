// TikTok Content Posting API, upload mode: the video lands in the account's TikTok
// inbox as a draft and Luca finishes the post in the app (trending sound, caption).
// No direct post (needs an app audit), no browser or app automation (banned by TikTok).
// Client key, client secret and OAuth tokens live in the macOS Keychain (service discord-bot).
// One-time login: npm run tiktok-connexion
import { execFile } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { open, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { trousseau } from './secrets.js';

export { trousseau };

export const API = 'https://open.tiktokapis.com/v2';
const AUTORISATION = 'https://www.tiktok.com/v2/auth/authorize/';
// Desktop app in the TikTok portal: only localhost redirects, PKCE required.
export const REDIRECTION = 'http://127.0.0.1:3455/callback/';
const SCOPES = 'user.info.basic,video.upload';
const MO = 2 ** 20;
const TYPES = { '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm' };
const ERREURS = {
  spam_risk_too_many_pending_share: '5 brouillons en attente max sur 24 h : publie ou supprime ceux de TikTok',
  access_token_invalid: 'connexion TikTok expirée : lance `npm run tiktok-connexion`',
  scope_not_authorized: 'scope video.upload non accordé : lance `npm run tiktok-connexion`',
  rate_limit_exceeded: 'trop de requêtes TikTok, réessaie dans une minute',
  spam_risk_user_banned_from_posting: 'TikTok bloque la publication sur ce compte',
};

// --- Electoral silence (Code électoral art. L49) ---

const lireTours = () => JSON.parse(readFileSync(new URL('../elections.json', import.meta.url), 'utf8')).tours;

const decaler = (jour, n) => new Date(Date.parse(`${jour}T00:00:00Z`) + n * 86_400_000).toISOString().slice(0, 10);

// Instant of 0 h in Paris on that day. The offset at 0 h UTC equals the one at
// Paris midnight: daylight saving changes happen at 2-3 h local time.
export function minuitParis(jour) {
  const utc = Date.parse(`${jour}T00:00:00Z`);
  const decalage = new Intl.DateTimeFormat('en-US', { timeZone: 'Europe/Paris', timeZoneName: 'longOffset' })
    .formatToParts(utc).find((p) => p.type === 'timeZoneName').value; // "GMT+02:00"
  const [, signe = '+', h = 0, m = 0] = decalage.match(/([+-])(\d\d):(\d\d)/) ?? [];
  return new Date(utc - (signe === '+' ? 1 : -1) * (h * 60 + Number(m)) * 60_000);
}

// The round whose silence covers `maintenant` ({ nom, debut, fin, confirme }), or null.
// Silence runs from 0 h the day before the first voting day (Saturday overseas)
// to the end of the last voting day, Paris time.
export function silence(maintenant = new Date(), tours = lireTours()) {
  for (const tour of tours) {
    const jours = [...tour.jours].sort();
    const debut = minuitParis(decaler(jours[0], -1));
    const fin = minuitParis(decaler(jours.at(-1), 1));
    if (maintenant >= debut && maintenant < fin) return { ...tour, debut, fin };
  }
  return null;
}

export const toursAConfirmer = (tours = lireTours()) => tours.filter((t) => !t.confirme).map((t) => t.nom);

export const dateParis = (date) => date.toLocaleString('fr-FR',
  { timeZone: 'Europe/Paris', weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' });

// --- OAuth (Login Kit for Desktop, scope video.upload) ---

function identifiants() {
  const client_key = trousseau.lire('tiktok-client-key');
  const client_secret = trousseau.lire('tiktok-client-secret');
  if (!client_key || !client_secret) throw new Error('client TikTok absent du trousseau (voir README, section TikTok)');
  return { client_key, client_secret };
}

const lireJetons = () => {
  const valeur = trousseau.lire('tiktok-jetons');
  return valeur ? JSON.parse(Buffer.from(valeur, 'base64').toString()) : null;
};

async function demanderJetons(parametres) {
  const reponse = await fetch(`${API}/oauth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ ...identifiants(), ...parametres }),
  });
  const r = await reponse.json().catch(() => ({}));
  if (!r.access_token) throw new Error(`OAuth TikTok refusé : ${r.error_description || r.error || `HTTP ${reponse.status}`}`);
  // The refresh token may change on each refresh: always keep the latest one.
  const jetons = {
    access_token: r.access_token, refresh_token: r.refresh_token, open_id: r.open_id, scope: r.scope,
    expire: Date.now() + r.expires_in * 1000, expireRefresh: Date.now() + r.refresh_expires_in * 1000,
  };
  trousseau.ecrire('tiktok-jetons', Buffer.from(JSON.stringify(jetons)).toString('base64'));
  return jetons;
}

export const connecte = () => (lireJetons()?.expireRefresh ?? 0) > Date.now();

// Valid access token (24 h), refreshed 5 min before expiry (refresh token: 365 days).
export async function jeton() {
  const jetons = lireJetons();
  if (!jetons || jetons.expireRefresh <= Date.now()) throw new Error('TikTok pas connecté : lance `npm run tiktok-connexion`');
  if (jetons.expire - Date.now() > 5 * 60_000) return jetons.access_token;
  return (await demanderJetons({ grant_type: 'refresh_token', refresh_token: jetons.refresh_token })).access_token;
}

export function urlAutorisation(client_key, verificateur, etat) {
  return `${AUTORISATION}?${new URLSearchParams({
    client_key, scope: SCOPES, redirect_uri: REDIRECTION, state: etat, response_type: 'code',
    code_challenge: createHash('sha256').update(verificateur).digest('hex'), // TikTok wants hex, not base64url
    code_challenge_method: 'S256',
  })}`;
}

// One-time flow: opens the TikTok consent page, catches the redirect on localhost.
async function connexion() {
  const { client_key } = identifiants();
  const verificateur = randomBytes(48).toString('base64url'); // 64 unreserved characters
  const etat = randomBytes(16).toString('hex');
  const url = urlAutorisation(client_key, verificateur, etat);
  const { port, pathname } = new URL(REDIRECTION);
  const code = await new Promise((resolve, reject) => {
    const serveur = createServer((req, res) => {
      const q = new URL(req.url, REDIRECTION);
      if (q.pathname !== pathname) return res.writeHead(404).end();
      const p = q.searchParams;
      const ok = p.get('state') === etat && p.get('code');
      res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' })
        .end(ok ? 'TikTok connecté, tu peux fermer cet onglet.' : 'Échec, regarde le terminal.');
      serveur.close();
      if (ok) resolve(p.get('code')); // searchParams already URL-decodes the code
      else reject(new Error(`autorisation refusée : ${p.get('error_description') || p.get('error') || 'état invalide'}`));
    }).listen(Number(port), '127.0.0.1', () => {
      console.log(`Ouvre cette page si le navigateur ne s'ouvre pas :\n${url}`);
      execFile('open', [url]);
    });
  });
  const jetons = await demanderJetons({ grant_type: 'authorization_code', code, redirect_uri: REDIRECTION, code_verifier: verificateur });
  if (!jetons.scope?.split(',').includes('video.upload')) console.warn(`Attention : scope video.upload absent (${jetons.scope})`);
  console.log(`TikTok connecté (scopes : ${jetons.scope}). Jetons rangés dans le trousseau.`);
}

// --- Upload to drafts ---

async function appel(chemin, corps) {
  const reponse = await fetch(`${API}${chemin}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${await jeton()}`, 'Content-Type': 'application/json; charset=UTF-8' },
    body: JSON.stringify(corps),
  });
  const r = await reponse.json().catch(() => ({}));
  const code = r.error?.code ?? `http_${reponse.status}`;
  if (code !== 'ok') {
    throw Object.assign(new Error(ERREURS[code] ?? `TikTok : ${code} ${r.error?.message ?? ''}`.trim()), { code }); // code: callers retry on limits
  }
  return r.data;
}

// Media transfer guide: up to 64 MB in one chunk; above that, 5-64 MB chunks,
// count = floor(size / chunk), the last chunk takes the rest (128 MB max).
export function decoupe(taille) {
  const morceau = taille <= 64 * MO ? taille : 10 * MO;
  const nombre = Math.floor(taille / morceau);
  const plages = Array.from({ length: nombre }, (_, i) => [i * morceau, i === nombre - 1 ? taille - 1 : (i + 1) * morceau - 1]);
  return { morceau, nombre, plages };
}

// Returns the publish_id. Refuses during electoral silence.
export async function envoyerBrouillon(chemin, maintenant = new Date()) {
  const tour = silence(maintenant);
  if (tour) throw new Error(`silence électoral (${tour.nom}) jusqu'au ${dateParis(tour.fin)}`);
  const type = TYPES[extname(chemin).toLowerCase()];
  if (!type) throw new Error('format refusé par TikTok (mp4, mov ou webm)');
  const { size } = await stat(chemin);
  if (!size || size > 4 * 2 ** 30) throw new Error('vidéo vide ou de plus de 4 Go');

  const { morceau, nombre, plages } = decoupe(size);
  const { publish_id, upload_url } = await appel('/post/publish/inbox/video/init/', {
    source_info: { source: 'FILE_UPLOAD', video_size: size, chunk_size: morceau, total_chunk_count: nombre },
  });
  const fichier = await open(chemin);
  try {
    for (const [debut, fin] of plages) { // chunks must go in order
      const tampon = Buffer.alloc(fin - debut + 1);
      await fichier.read(tampon, 0, tampon.length, debut);
      const reponse = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': type, 'Content-Range': `bytes ${debut}-${fin}/${size}` },
        body: tampon,
      });
      if (!reponse.ok) throw new Error(`morceau ${debut}-${fin} refusé (HTTP ${reponse.status})`);
    }
  } finally {
    await fichier.close();
  }
  return publish_id;
}

// Statuses meaning the draft is in the TikTok inbox.
export const ARRIVE = ['SEND_TO_USER_INBOX', 'PUBLISH_COMPLETE'];

// One status check ({ status, fail_reason }). TikTok took 15 to 45 min to go from
// PROCESSING_UPLOAD to SEND_TO_USER_INBOX in sandbox, so callers check again later.
export const statutBrouillon = (publishId) => appel('/post/publish/status/fetch/', { publish_id: publishId });

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (process.argv[2] !== 'connexion') {
    console.error('Usage : node src/tiktok.js connexion');
    process.exit(1);
  }
  await connexion();
}
