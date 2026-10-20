#!/usr/bin/env node
/**
 * Export an HTML poster/design to PNG using Playwright.
 * Usage: node export-html-to-png.js <html-path> <output-png> [width] [height]
 * 
 * Defaults: 1080x1350 (Instagram 4:5)
 * Common sizes:
 *   1080x1350  Instagram post (4:5)
 *   1080x1920  Instagram story / TikTok (9:16)
 *   1080x1080  Square
 *   1280x720   YouTube thumbnail (16:9)
 *   1920x1080  Landscape HD
 */

const path = require('path');

// Try multiple Playwright locations
let chromium;
try {
  chromium = require('/home/ubuntu/.hermes/hermes-agent/node_modules/playwright').chromium;
} catch {
  chromium = require('playwright').chromium;
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node export-html-to-png.js <html-path> <output-png> [width] [height]');
  process.exit(1);
}

const htmlPath = path.resolve(args[0]);
const outputPath = path.resolve(args[1]);
const width = parseInt(args[2]) || 1080;
const height = parseInt(args[3]) || 1350;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width, height });
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(2000); // let animations/particles settle
  await page.screenshot({ path: outputPath, fullPage: false });
  await browser.close();
  console.log(`Exported: ${outputPath} (${width}x${height})`);
})();
