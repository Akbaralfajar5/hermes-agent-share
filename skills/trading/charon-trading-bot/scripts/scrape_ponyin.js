// Run this in browser_console on https://www.ponyin.id/
// Extracts ALL topic content from the SPA in one shot
// Returns JSON with index → {title, text} for all h2 sections

(() => {
  const all = Array.from(document.querySelectorAll('h2'));
  const result = {};
  all.forEach((h, i) => {
    const p = h.parentElement;
    if (p && p.innerText.length > 150) {
      result[i] = { title: h.innerText.replace(/\n/g,' ').trim(), text: p.innerText };
    }
  });
  return JSON.stringify(result);
})();

// NOTE: ponyin.id is a React SPA — all content is already in the DOM on load.
// No need to click through each topic. One browser_console call gets everything.
// Topics 0–10 = Vol.1 (Bundle Basics), 11–21 = Vol.2 Advance, 22–23 = Spaces/PnL
