import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Navigating to http://localhost:5180 ...');
  await page.goto('http://localhost:5180', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Click Preferences button
  console.log('Clicking Preferences / Settings button...');
  const settingsBtn = page.locator('button[title*="Preferences"]');
  await settingsBtn.click();
  await page.waitForTimeout(1000);

  // Take screenshot of AI tab
  const shot1 = path.join(__dirname, '..', 'preferences_ai_tab.png');
  await page.screenshot({ path: shot1, fullPage: true });
  console.log(`Saved screenshot 1 to: ${shot1}`);

  // Switch to Drop Folder tab
  console.log('Switching to Drop Folder tab...');
  const dropTab = page.locator('button', { hasText: 'Drop Folder / Import' });
  await dropTab.click();
  await page.waitForTimeout(1000);

  const shot2 = path.join(__dirname, '..', 'preferences_drop_folder_tab.png');
  await page.screenshot({ path: shot2, fullPage: true });
  console.log(`Saved screenshot 2 to: ${shot2}`);

  await browser.close();
  console.log('Preferences UI test complete!');
}

main().catch(console.error);
