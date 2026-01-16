#!/usr/bin/env node

/**
 * Logo generator for AR-INFRA CLI
 * Captures oh-my-logo output from stdout
 */

import { renderFilled } from 'oh-my-logo';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { Writable } from 'stream';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CONFIG = {
  text: 'AR-INFRA',
  palette: 'ocean',
  letterSpacing: 0,
  outputPath: join(__dirname, '..', 'src', 'ar_infra', 'cli', 'resources', 'banner.txt'),
} as const;

/**
 * Captures stdout output
 */
class StdoutCapture extends Writable {
  chunks: Buffer[] = [];

  _write(chunk: Buffer, encoding: string, callback: () => void): void {
    this.chunks.push(chunk);
    callback();
  }

  getOutput(): string {
    return Buffer.concat(this.chunks).toString('utf-8');
  }
}

function ensureDirectoryExists(filePath: string): void {
  const dir = dirname(filePath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

async function generateLogo(): Promise<void> {
  try {
    console.log('[INFO] Generating AR-INFRA banner...');

    process.env.FORCE_COLOR = '3';
    process.env.COLORTERM = 'truecolor';
    process.env.TERM = 'xterm-256color';

    const originalIsTTY = process.stdout.isTTY;
    Object.defineProperty(process.stdout, 'isTTY', {
      value: true,
      configurable: true,
      writable: true,
    });

    const capture = new StdoutCapture();
    const originalWrite = process.stdout.write.bind(process.stdout);

    process.stdout.write = (chunk: any, encoding?: any, callback?: any): boolean => {
      capture.write(chunk, encoding, callback);
      return true;
    };

    await renderFilled(CONFIG.text, {
      palette: CONFIG.palette,
      letterSpacing: CONFIG.letterSpacing,
    });

    process.stdout.write = originalWrite;

    Object.defineProperty(process.stdout, 'isTTY', {
      value: originalIsTTY,
      configurable: true,
      writable: true,
    });

    const logo = capture.getOutput();

    if (!logo || typeof logo !== 'string') {
      throw new Error(`Invalid logo output: ${typeof logo}`);
    }

    const trimmedLogo = logo.trim();
    const hasAnsiCodes = trimmedLogo.includes('\x1b[') || trimmedLogo.includes('\u001b[');

    console.log('[DEBUG] Generated logo (preview):');
    console.log(trimmedLogo);
    console.log('');
    console.log(`[INFO] Logo length: ${trimmedLogo.length} characters`);
    console.log(`[INFO] Contains ANSI codes: ${hasAnsiCodes}`);

    if (!hasAnsiCodes) {
      console.log('[WARNING] No ANSI codes detected. Banner will be monochrome.');
    }

    ensureDirectoryExists(CONFIG.outputPath);

    writeFileSync(CONFIG.outputPath, trimmedLogo, { encoding: 'utf-8' });

    console.log('[SUCCESS] Banner text file generated successfully');
    console.log(`[INFO] Output: ${CONFIG.outputPath}`);

    if (!existsSync(CONFIG.outputPath)) {
      throw new Error('Generated file does not exist');
    }

    const buffer = Buffer.from(trimmedLogo.substring(0, 100));
    console.log('[DEBUG] First 100 bytes (hex):');
    console.log(buffer.toString('hex').match(/.{1,2}/g)?.join(' '));

    console.log('[SUCCESS] File verified');

  } catch (error) {
    console.error('[ERROR] Failed to generate logo:', error);
    if (error instanceof Error) {
      console.error('[ERROR] Stack trace:', error.stack);
    }
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateLogo().catch((error: Error) => {
    console.error('[FATAL] Unhandled error:', error.message);
    process.exit(1);
  });
}
