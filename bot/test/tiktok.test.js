// TikTok module without a TikTok account: fake Keychain, fake fetch, fake Discord interaction.
import assert from 'node:assert/strict';
import { access, mkdir, mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { beforeEach, test } from 'node:test';

const PROJET = await mkdtemp(join(tmpdir(), 'tiktok-test-'));
const DOSSIER = join(PROJET, 'a-publier');
await mkdir(DOSSIER);
process.env.TIKTOK_DOSSIER = DOSSIER;
const tiktok = await import('../src/tiktok.js');
const module = await import('../modules/tiktok.js');

const TOURS = [{ nom: 'Test, 1er tour', jours: ['2027-04-10', '2027-04-11'], confirme: false }];
const MO = 2 ** 20;

// Fake Keychain: tokens stored as base64 JSON, like the real one.
let coffre;
tiktok.trousseau.lire = (compte) => coffre[compte] ?? null;
tiktok.trousseau.ecrire = (compte, valeur) => { coffre[compte] = valeur; };
const jetons = (j) => Buffer.from(JSON.stringify(j)).toString('base64');

// Fake TikTok API: records every request, answers by URL.
let requetes;
let reponses;
globalThis.fetch = async (url, options = {}) => {
  requetes.push({ url: String(url), ...options });
  const corps = reponses(String(url), options);
  return new Response(JSON.stringify(corps ?? {}), { status: corps?.status ?? 200 });
};
const ok = (data) => ({ data, error: { code: 'ok', message: '' } });

beforeEach(() => {
  requetes = [];
  coffre = {
    'tiktok-client-key': 'cle', 'tiktok-client-secret': 'secret',
    'tiktok-jetons': jetons({ access_token: 'acces', refresh_token: 'rafraichi', expire: Date.now() + 3_600_000, expireRefresh: Date.now() + 86_400_000 }),
  };
  reponses = (url) => {
    if (url.endsWith('/inbox/video/init/')) return ok({ publish_id: 'v_inbox_file~1', upload_url: 'https://upload.test/video?x=1' });
    if (url.endsWith('/status/fetch/')) return ok({ status: 'SEND_TO_USER_INBOX' });
    if (url.startsWith('https://upload.test/')) return {};
    throw new Error(`URL inattendue ${url}`);
  };
});

test('minuit à Paris, heure d’hiver et d’été', () => {
  assert.equal(tiktok.minuitParis('2027-01-15').toISOString(), '2027-01-14T23:00:00.000Z');
  assert.equal(tiktok.minuitParis('2027-04-10').toISOString(), '2027-04-09T22:00:00.000Z');
  // Days of the daylight saving change: midnight is still on the old offset.
  assert.equal(tiktok.minuitParis('2027-03-28').toISOString(), '2027-03-27T23:00:00.000Z');
  assert.equal(tiktok.minuitParis('2026-10-25').toISOString(), '2026-10-24T22:00:00.000Z');
});

test('silence électoral : de la veille du premier jour à 0 h à la fin du dernier jour', () => {
  const a = (iso) => tiktok.silence(new Date(iso), TOURS);
  assert.equal(a('2027-04-08T21:59:59Z'), null); // Thursday 23:59:59 Paris
  assert.equal(a('2027-04-08T22:00:00Z')?.nom, 'Test, 1er tour'); // Friday 0 h Paris
  assert.ok(a('2027-04-11T21:59:59Z')); // Sunday 23:59:59 Paris
  assert.equal(a('2027-04-11T22:00:00Z'), null); // Monday 0 h Paris
});

test('elections.json : tours lisibles et marqués à confirmer', () => {
  assert.equal(tiktok.toursAConfirmer().length, 2);
  assert.ok(tiktok.silence(new Date('2027-04-10T12:00:00Z')));
  assert.ok(tiktok.silence(new Date('2027-04-24T12:00:00Z')));
  assert.equal(tiktok.silence(new Date('2026-10-26T12:00:00Z')), null);
});

test('découpe selon le guide TikTok', () => {
  assert.deepEqual(tiktok.decoupe(3 * MO), { morceau: 3 * MO, nombre: 1, plages: [[0, 3 * MO - 1]] });
  assert.equal(tiktok.decoupe(64 * MO).nombre, 1);
  const grand = tiktok.decoupe(95 * MO + 123);
  assert.equal(grand.morceau, 10 * MO);
  assert.equal(grand.nombre, 9);
  assert.deepEqual(grand.plages.at(-1), [80 * MO, 95 * MO + 122]); // last chunk takes the rest
  for (const [debut, fin] of grand.plages.slice(0, -1)) assert.equal(fin - debut + 1, 10 * MO);
});

test('envoi en brouillon : init puis PUT avec les bons en-têtes', async () => {
  const video = join(DOSSIER, 'requete.mp4');
  await writeFile(video, Buffer.alloc(1234, 7));
  assert.equal(await tiktok.envoyerBrouillon(video, new Date('2026-11-01T12:00:00Z')), 'v_inbox_file~1');

  const [init, put] = requetes;
  assert.equal(init.url, 'https://open.tiktokapis.com/v2/post/publish/inbox/video/init/');
  assert.equal(init.method, 'POST');
  assert.equal(init.headers.Authorization, 'Bearer acces');
  assert.deepEqual(JSON.parse(init.body), { source_info: { source: 'FILE_UPLOAD', video_size: 1234, chunk_size: 1234, total_chunk_count: 1 } });
  assert.equal(put.url, 'https://upload.test/video?x=1');
  assert.equal(put.method, 'PUT');
  assert.equal(put.headers['Content-Type'], 'video/mp4');
  assert.equal(put.headers['Content-Range'], 'bytes 0-1233/1234');
  assert.equal(put.body.length, 1234);
});

test('envoi refusé pendant le silence électoral, sans appel à TikTok', async () => {
  await assert.rejects(tiktok.envoyerBrouillon(join(DOSSIER, 'requete.mp4'), new Date('2027-04-10T12:00:00Z')), /silence électoral/);
  assert.equal(requetes.length, 0);
});

test('jeton expiré : rafraîchi et nouveau refresh token gardé', async () => {
  coffre['tiktok-jetons'] = jetons({ access_token: 'vieux', refresh_token: 'r1', expire: Date.now() + 60_000, expireRefresh: Date.now() + 86_400_000 });
  reponses = () => ({ access_token: 'neuf', refresh_token: 'r2', expires_in: 86400, refresh_expires_in: 31536000, open_id: 'o', scope: 'video.upload' });
  assert.equal(await tiktok.jeton(), 'neuf');
  const [req] = requetes;
  assert.equal(req.url, 'https://open.tiktokapis.com/v2/oauth/token/');
  assert.equal(req.headers['Content-Type'], 'application/x-www-form-urlencoded');
  assert.deepEqual(Object.fromEntries(req.body), { client_key: 'cle', client_secret: 'secret', grant_type: 'refresh_token', refresh_token: 'r1' });
  const garde = JSON.parse(Buffer.from(coffre['tiktok-jetons'], 'base64').toString());
  assert.equal(garde.refresh_token, 'r2');
  assert.ok(garde.expire > Date.now() + 86_000_000);
});

test('pas de jetons : message qui dit quoi faire', async () => {
  delete coffre['tiktok-jetons'];
  await assert.rejects(tiktok.jeton(), /npm run tiktok-connexion/);
  assert.equal(tiktok.connecte(), false);
});

test('erreur TikTok traduite (5 brouillons en attente)', async () => {
  reponses = () => ({ status: 403, error: { code: 'spam_risk_too_many_pending_share', message: '' } });
  await assert.rejects(tiktok.envoyerBrouillon(join(DOSSIER, 'requete.mp4'), new Date('2026-11-01T12:00:00Z')), /5 brouillons/);
});

test('URL d’autorisation : PKCE en SHA-256 hexadécimal', () => {
  const url = new URL(tiktok.urlAutorisation('cle', 'a'.repeat(64), 'etat'));
  assert.equal(url.origin + url.pathname, 'https://www.tiktok.com/v2/auth/authorize/');
  const p = Object.fromEntries(url.searchParams);
  assert.equal(p.scope, 'user.info.basic,video.upload');
  assert.equal(p.redirect_uri, 'http://127.0.0.1:3455/callback/');
  assert.equal(p.response_type, 'code');
  assert.equal(p.code_challenge_method, 'S256');
  assert.match(p.code_challenge, /^[0-9a-f]{64}$/);
});

test('proposition Discord : boutons et texte', () => {
  const [valider, refuser] = module.boutons('video-1').toJSON().components;
  assert.equal(valider.custom_id, 'tiktok:valider:video-1');
  assert.equal(refuser.custom_id, 'tiktok:refuser:video-1');
  const texte = module.texteProposition('aura_nb', { legende: 'Le vote, c’est *maintenant*', hashtags: ['#lfi', '#vote'] });
  assert.match(texte, /^## 🎬 TikTok à valider\n\*\*aura\\_nb\*\*/);
  assert.match(texte, /\\\*maintenant\\\*\n#lfi #vote/);
});

// Fake button click: Discord message and interaction with only what the module uses.
function clic(action, nom) {
  const traces = { update: [], edits: [], envois: [] };
  const message = {
    id: 'm1',
    channelId: 'c1',
    content: '## 🎬 TikTok à valider\n**x**',
    edit: async (m) => { traces.edits.push(m); message.content = m.content; },
    channel: { send: async (m) => traces.envois.push(m) },
  };
  const interaction = { customId: `tiktok:${action}:${nom}`, message, update: async (m) => { traces.update.push(m); message.content = m.content; } };
  return { interaction, traces };
}

// Fake Discord client that finds the clicked message again.
const client = (message) => ({ channels: { fetch: async () => ({ messages: { fetch: async () => message } }) } });

test('clic Valider : envoi, légende seule, message mis à jour quand le brouillon arrive', async () => {
  await mkdir(join(DOSSIER, 'proposees'), { recursive: true });
  await writeFile(join(DOSSIER, 'proposees', 'clip.mp4'), Buffer.alloc(100));
  await writeFile(join(DOSSIER, 'proposees', 'clip.json'), JSON.stringify({ legende: 'Va voter', hashtags: ['#lfi'] }));
  let statut = 'PROCESSING_UPLOAD';
  const tiktokApi = reponses;
  reponses = (url, options) => (url.endsWith('/status/fetch/') ? ok({ status: statut }) : tiktokApi(url, options));
  const { interaction, traces } = clic('valider', 'clip');
  await module.onButton(interaction);
  assert.deepEqual(traces.update[0].components, []); // buttons gone during upload
  assert.match(traces.update[0].content, /⏳ Envoi/);
  assert.match(traces.edits.at(-1).content, /⏳ Envoyée, TikTok la traite/);
  assert.deepEqual(traces.envois, ['Va voter\n#lfi']);
  assert.deepEqual((await readdir(join(DOSSIER, 'envoyees'))).sort(), ['clip.json', 'clip.mp4', 'clip.suivi.json']);

  await module.suivre(client(interaction.message)); // TikTok still processing: nothing changes
  assert.equal(traces.edits.length, 1);
  statut = 'SEND_TO_USER_INBOX';
  await module.suivre(client(interaction.message));
  assert.match(traces.edits.at(-1).content, /\*\*x\*\*\n\n✅ Dans tes brouillons TikTok/);
  assert.equal(traces.edits.at(-1).content.match(/⏳/), null);
  assert.deepEqual((await readdir(join(DOSSIER, 'envoyees'))).sort(), ['clip.json']); // video deleted once delivered
});

test('brouillon rejeté par TikTok : raison affichée, suivi arrêté', async () => {
  await writeFile(join(DOSSIER, 'envoyees', 'rejet.suivi.json'), JSON.stringify({ publishId: 'v~2', salon: 'c1', message: 'm1', depuis: Date.now() }));
  reponses = () => ok({ status: 'FAILED', fail_reason: 'file_format_check_failed' });
  const { interaction, traces } = clic('valider', 'rejet');
  await module.suivre(client(interaction.message));
  assert.match(traces.edits.at(-1).content, /❌ TikTok a rejeté la vidéo : file_format_check_failed/);
  assert.ok(!(await readdir(join(DOSSIER, 'envoyees'))).includes('rejet.suivi.json'));
});

test('clic Valider en échec : erreur affichée et boutons remis', async () => {
  await writeFile(join(DOSSIER, 'proposees', 'rate.mp4'), Buffer.alloc(100));
  await writeFile(join(DOSSIER, 'proposees', 'rate.json'), '{}');
  delete coffre['tiktok-jetons'];
  const { interaction, traces } = clic('valider', 'rate');
  await module.onButton(interaction);
  assert.match(traces.edits.at(-1).content, /❌ TikTok pas connecté/);
  assert.equal(traces.edits.at(-1).components.length, 1);
  assert.ok((await readdir(join(DOSSIER, 'proposees'))).includes('rate.mp4'));
});

test('clic Refuser : fichiers dans refusees', async () => {
  const { interaction, traces } = clic('refuser', 'rate');
  await module.onButton(interaction);
  assert.match(traces.update[0].content, /🗑️ Refusée$/);
  assert.deepEqual((await readdir(join(DOSSIER, 'refusees'))).sort(), ['rate.json', 'rate.mp4']);
});

test('clic d’un autre module ignoré', async () => {
  const { interaction, traces } = clic('x', 'y');
  interaction.customId = 'valider';
  await module.onButton(interaction);
  assert.equal(traces.update.length + traces.edits.length, 0);
});

test('limite TikTok : vidéo en file d’attente puis envoyée toute seule', async () => {
  await writeFile(join(DOSSIER, 'proposees', 'file.mp4'), Buffer.alloc(100));
  await writeFile(join(DOSSIER, 'proposees', 'file.json'), '{}');
  const tiktokApi = reponses;
  reponses = (url, options) => (url.endsWith('/inbox/video/init/')
    ? { status: 403, error: { code: 'spam_risk_too_many_pending_share', message: '' } } : tiktokApi(url, options));
  const { interaction, traces } = clic('valider', 'file');
  await module.onButton(interaction);
  assert.match(traces.edits.at(-1).content, /⏳ En file d'attente : 5 brouillons/);
  assert.deepEqual(traces.edits.at(-1).components, []);
  assert.ok((await readdir(join(DOSSIER, 'proposees'))).includes('file.attente.json'));

  await module.relancer(client(interaction.message)); // wait not over: nothing sent
  assert.equal(traces.edits.length, 1);
  await writeFile(join(DOSSIER, 'proposees', 'file.attente.json'), JSON.stringify({ salon: 'c1', message: 'm1', prochain: 0 }));
  reponses = tiktokApi;
  await module.relancer(client(interaction.message));
  assert.match(traces.edits.at(-1).content, /⏳ Envoyée, TikTok la traite/);
  assert.equal(traces.edits.at(-1).content.match(/En file/), null);
  assert.ok(!(await readdir(join(DOSSIER, 'proposees'))).includes('file.attente.json'));
  assert.ok((await readdir(join(DOSSIER, 'envoyees'))).includes('file.mp4'));
});

test('file d’attente : la vidéo la moins proche des derniers envois part en premier', () => {
  const recents = ['aubry-G2', 'boyard-G1', 'melenchon-A6'];
  assert.equal(module.choisir(['obono-G4', 'melenchon-C4', 'coquerel-K2'], recents), 'coquerel-K2'); // new style and figure
  assert.equal(module.choisir(['obono-G4', 'melenchon-A1'], recents), 'melenchon-A1'); // one A recently beats two G
  assert.equal(module.choisir(['panot-L1', 'obono-V2'], ['guette-A4']), 'obono-V2'); // L1 is an aura (A)
  assert.equal(module.choisir(['a-K1', 'b-K2'], []), 'a-K1'); // tie: queue order kept
});

test('limite TikTok : toute la file attend, pas seulement la vidéo refusée', async () => {
  const proposees = join(DOSSIER, 'proposees');
  await writeFile(join(proposees, 'autre-Z9.attente.json'), JSON.stringify({ salon: 'c1', message: 'm2', prochain: 0 }));
  await writeFile(join(proposees, 'pause.mp4'), Buffer.alloc(100));
  await writeFile(join(proposees, 'pause.json'), '{}');
  const tiktokApi = reponses;
  reponses = (url, options) => (url.endsWith('/inbox/video/init/')
    ? { status: 403, error: { code: 'spam_risk_too_many_pending_share', message: '' } } : tiktokApi(url, options));
  await module.onButton(clic('valider', 'pause').interaction);
  const { prochain } = JSON.parse(await readFile(join(proposees, 'autre-Z9.attente.json'), 'utf8'));
  assert.ok(prochain > Date.now() + 29 * 60_000);
  reponses = tiktokApi;
  for (const f of ['autre-Z9.attente.json', 'pause.attente.json', 'pause.mp4', 'pause.json']) await rm(join(proposees, f), { force: true });
});

test('brouillon arrivé : vidéo, HD et fichiers de travail supprimés, rien hors du projet', async () => {
  const dehors = `${PROJET}-dehors.txt`;
  await mkdir(join(PROJET, 'hd'), { recursive: true });
  await mkdir(join(PROJET, 'gen', 'X', 'out'), { recursive: true });
  await writeFile(join(PROJET, 'hd', 'HD-X.mp4'), 'x');
  await writeFile(join(PROJET, 'gen', 'X', 'out', 'plan.mov'), 'x');
  await writeFile(dehors, 'x');
  await writeFile(join(DOSSIER, 'envoyees', 'net.mp4'), 'x');
  await writeFile(join(DOSSIER, 'envoyees', 'net.json'),
    JSON.stringify({ apres_envoi: ['hd/HD-X.mp4', 'gen/X/out', `../${dehors.split('/').pop()}`] }));
  await writeFile(join(DOSSIER, 'envoyees', 'net.suivi.json'), JSON.stringify({ publishId: 'v~3', salon: 'c1', message: 'm1', depuis: Date.now() }));
  const { interaction } = clic('valider', 'net');
  await module.suivre(client(interaction.message));
  const envoyees = await readdir(join(DOSSIER, 'envoyees'));
  assert.ok(!envoyees.includes('net.mp4') && !envoyees.includes('net.suivi.json') && envoyees.includes('net.json'));
  await assert.rejects(access(join(PROJET, 'hd', 'HD-X.mp4')));
  await assert.rejects(access(join(PROJET, 'gen', 'X', 'out')));
  await access(dehors); // outside the project: kept
});
