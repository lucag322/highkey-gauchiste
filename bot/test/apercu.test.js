// Preview buttons without Discord: fake interaction, verdicts written to a temp folder.
import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

const DOSSIER = await mkdtemp(join(tmpdir(), 'apercu-test-'));
process.env.APERCU_DOSSIER = DOSSIER;
const apercu = await import('../modules/apercu.js');

function clic(customId, content = '## 🎬 Bompard v2\n**Aperçu 15 s**') {
  const traces = [];
  const interaction = { customId, message: { content }, update: async (m) => traces.push(m) };
  return { interaction, traces };
}

test('boutons de l’aperçu', () => {
  const [valider, refaire] = apercu.boutons('A2').toJSON().components;
  assert.equal(valider.custom_id, 'apercu:valider:A2');
  assert.equal(refaire.custom_id, 'apercu:refaire:A2');
});

test('Valider puis À refaire : verdict noté, message mis à jour, dernier clic gagne', async () => {
  const premier = clic('apercu:valider:A2');
  await apercu.onButton(premier.interaction);
  assert.match(premier.traces[0].content, /\*\*Aperçu 15 s\*\*\n\n✅ Validé/);
  assert.equal((await apercu.lireValidations()).A2.statut, 'validé');

  const second = clic('apercu:refaire:A2', premier.traces[0].content);
  await apercu.onButton(second.interaction);
  assert.equal(second.traces[0].content.match(/✅/), null);
  assert.match(second.traces[0].content, /🔁 À refaire/);
  const fichier = JSON.parse(await readFile(join(DOSSIER, 'validations.json'), 'utf8'));
  assert.equal(fichier.A2.statut, 'à refaire');
});

test('clic d’un autre module ignoré', async () => {
  const { interaction, traces } = clic('tiktok:valider:x');
  await apercu.onButton(interaction);
  assert.equal(traces.length, 0);
});
