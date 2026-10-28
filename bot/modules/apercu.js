// Low-quality previews of the account's edits, posted by Claude with
// `npm run apercu -- <id> <video.mp4> "<text>"`, with Valider / À refaire buttons.
// A click records the verdict in preview/validations.json; Claude reads it before the
// HD finish (Resolve only runs in a Claude session, never in the bot).
// Buttons carry the video id, so they keep working after a bot restart.
import { execFile } from 'node:child_process';
import { readFile, rm, stat, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { ActionRowBuilder, ButtonBuilder, ButtonStyle } from 'discord.js';

const run = promisify(execFile);
const DOSSIER = process.env.APERCU_DOSSIER ?? join(homedir(), 'Movies/highkey-gauchiste/preview');
const VALIDATIONS = join(DOSSIER, 'validations.json');
const MAX = 9 * 2 ** 20; // Discord caps bot uploads at 10 MB
const STATUT = /\n\n(✅|🔁) [\s\S]*$/;

export const boutons = (id) => new ActionRowBuilder().addComponents(
  new ButtonBuilder().setCustomId(`apercu:valider:${id}`).setLabel('Valider').setEmoji('✅').setStyle(ButtonStyle.Success),
  new ButtonBuilder().setCustomId(`apercu:refaire:${id}`).setLabel('À refaire').setEmoji('🔁').setStyle(ButtonStyle.Secondary),
);

export const lireValidations = async () => JSON.parse(await readFile(VALIDATIONS, 'utf8').catch(() => '{}'));

const VERDICTS = {
  valider: { statut: 'validé', texte: '✅ Validé\n-# Dis « lance les HD » à Claude.' },
  refaire: { statut: 'à refaire', texte: '🔁 À refaire\n-# Dis à Claude ce qui ne va pas.' },
};

export async function onButton(interaction) {
  const [prefixe, action, ...reste] = interaction.customId.split(':');
  const verdict = VERDICTS[action];
  if (prefixe !== 'apercu' || !verdict) return;
  const id = reste.join(':');
  const validations = await lireValidations();
  validations[id] = { statut: verdict.statut, date: new Date().toISOString() };
  await writeFile(VALIDATIONS, JSON.stringify(validations, null, 2));
  // Buttons kept: Luca can change his mind.
  await interaction.update({ content: `${interaction.message.content.replace(STATUT, '')}\n\n${verdict.texte}` });
}

// CLI: post a preview with its buttons (the bot process handles the clicks).
async function poster(id, video, texte) {
  const { REST, Routes } = await import('discord.js');
  const { config, token } = await import('../src/secrets.js');
  let fichier = video;
  if ((await stat(video)).size > MAX) { // smaller H.264 copy, only for Discord
    fichier = join(tmpdir(), `apercu-${id}-${Date.now()}.mp4`);
    await run('ffmpeg', ['-v', 'error', '-y', '-i', video, '-vf', "scale='min(720,iw)':-2", '-c:v', 'libx264', '-preset', 'veryfast',
      '-crf', '28', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-fs', `${MAX}`, fichier], { timeout: 300_000 });
  }
  try {
    await new REST().setToken(token()).post(Routes.channelMessages(config.channels.general), {
      body: { content: texte, components: [boutons(id).toJSON()] },
      files: [{ name: basename(video), data: await readFile(fichier) }],
    });
  } finally {
    if (fichier !== video) await rm(fichier, { force: true });
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [id, video, texte] = process.argv.slice(2);
  if (!id || !video || !texte) {
    console.error('Usage : npm run apercu -- <id> <video.mp4> "<texte>"');
    process.exit(1);
  }
  await poster(id, video, texte);
  console.log(`aperçu ${id} posté`);
}
