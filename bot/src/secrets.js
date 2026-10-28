// The bot token lives in the macOS Keychain, never in the repo.
// Save it once with: security add-generic-password -U -s discord-bot -a token -w
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

export function token() {
  if (process.env.DISCORD_TOKEN) return process.env.DISCORD_TOKEN;
  try {
    return execFileSync('security', ['find-generic-password', '-s', 'discord-bot', '-a', 'token', '-w'], { encoding: 'utf8' }).trim();
  } catch {
    throw new Error('Token introuvable : lance `security add-generic-password -U -s discord-bot -a token -w` puis colle le token.');
  }
}

export const config = JSON.parse(readFileSync(new URL('../config.json', import.meta.url), 'utf8'));
// Other secrets (TikTok, Meta) in the same Keychain service; tests replace these two methods.
export const trousseau = {
  lire(compte) {
    try {
      return execFileSync('security', ['find-generic-password', '-s', 'discord-bot', '-a', compte, '-w'],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    } catch {
      return null;
    }
  },
  // Through `security -i` on stdin so the value never shows in the process list.
  // valeur must be a single word (base64 here).
  ecrire(compte, valeur) {
    execFileSync('security', ['-i'], { input: `add-generic-password -U -s discord-bot -a ${compte} -w ${valeur}\n` });
  },
};

