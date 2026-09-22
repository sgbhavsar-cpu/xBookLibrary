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

  // 1. Find Frank Herbert in the Tag Browser
  console.log('Clicking "Frank Herbert" once -> should become + (Include)...');
  const frankHerbertRow = page.locator('.tag-tree-row', { hasText: 'Frank Herbert' });
  await frankHerbertRow.click();
  await page.waitForTimeout(1000);

  // Take screenshot with Frank Herbert included
  const shot1 = path.join(__dirname, '..', 'tag_tree_included.png');
  await page.screenshot({ path: shot1, fullPage: true });
  console.log(`Saved screenshot 1 to: ${shot1}`);

  // 2. Click Frank Herbert again -> should become - (Exclude)
  console.log('Clicking "Frank Herbert" again -> should become - (Exclude)...');
  await frankHerbertRow.click();
  await page.waitForTimeout(1000);

  const shot2 = path.join(__dirname, '..', 'tag_tree_excluded.png');
  await page.screenshot({ path: shot2, fullPage: true });
  console.log(`Saved screenshot 2 to: ${shot2}`);

  // 3. Click again -> Neutral (Clear)
  console.log('Clicking "Frank Herbert" again -> should return to Neutral...');
  await frankHerbertRow.click();
  await page.waitForTimeout(1000);

  // 4. Test Tag search input in Tag Browser
  console.log('Typing "cyber" into Tag Browser search input...');
  const searchInput = page.locator('input[placeholder="Filter categories / tags..."]');
  await searchInput.fill('cyber');
  await page.waitForTimeout(1000);

  const shot3 = path.join(__dirname, '..', 'tag_tree_search_filtered.png');
  await page.screenshot({ path: shot3, fullPage: true });
  console.log(`Saved screenshot 3 to: ${shot3}`);

  await browser.close();
  console.log('Interactive Tag Browser verification complete!');
}

main().catch(console.error);
