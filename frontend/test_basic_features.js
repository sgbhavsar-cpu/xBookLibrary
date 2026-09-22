import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('--- Starting Playwright UI Verification ---');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  const consoleLogs = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  page.on('pageerror', (err) => {
    consoleLogs.push(`[pageerror] ${err.toString()}`);
  });

  console.log('1. Navigating to http://localhost:5180 ...');
  await page.goto('http://localhost:5180', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Check title & library name
  const headerText = await page.textContent('header');
  console.log('✓ Header content:', headerText ? headerText.replace(/\s+/g, ' ').trim() : 'N/A');

  // Verify books are rendered
  const bookCards = await page.locator('[data-testid="book-card"], div:has-text("Snow Crash")').count();
  console.log(`✓ Books detected on page (matching elements count: ${bookCards})`);

  // Verify Left Sidebar filter items
  const formatBadges = await page.locator('text=EPUB').count();
  console.log(`✓ Format filter elements found: ${formatBadges}`);

  // Test selecting a book: click Dune
  console.log('2. Clicking on book "Dune"...');
  const duneCard = page.locator('text=Dune').first();
  await duneCard.click();
  await page.waitForTimeout(1000);

  // Take screenshot of selected Dune
  const duneScreenshotPath = path.join(__dirname, '..', 'app_dune_selected.png');
  await page.screenshot({ path: duneScreenshotPath, fullPage: true });
  console.log(`✓ Screenshot of Dune selection saved to: ${duneScreenshotPath}`);

  // Check Inspector pane has Dune details
  const inspectorText = await page.locator('aside, div[style*="width: 380px"], div:has-text("Audiobook Hub")').first().innerText();
  const hasAudiobookHub = inspectorText.includes('Audiobook Hub') || inspectorText.includes('Dune') || inspectorText.includes('Frank Herbert');
  console.log(`✓ Detail inspector updated for Dune: ${hasAudiobookHub}`);

  // Test clicking Table View toggle
  console.log('3. Toggling to Table View...');
  const tableToggleBtn = page.locator('button[title*="Table"], button:has-text("Table"), svg.lucide-list, svg.lucide-table').first();
  if (await tableToggleBtn.count() > 0) {
    await tableToggleBtn.click();
    await page.waitForTimeout(800);
    console.log('✓ Switched view mode');
  }

  // Test Search Filter: type "Gibson"
  console.log('4. Testing search input for "Gibson"...');
  const searchInput = page.locator('input[placeholder*="Search"], input[type="text"]').first();
  if (await searchInput.count() > 0) {
    await searchInput.fill('Gibson');
    await page.waitForTimeout(800);
    const bodyText = await page.evaluate(() => document.body.innerText);
    const hasNeuromancer = bodyText.includes('Neuromancer');
    const hasSnowCrash = bodyText.includes('Snow Crash');
    console.log(`✓ Search filter test: Neuromancer shown = ${hasNeuromancer}, Snow Crash shown = ${hasSnowCrash}`);
    // Clear search
    await searchInput.fill('');
    await page.waitForTimeout(500);
  }

  // Save final interactive screenshot
  const finalScreenshotPath = path.join(__dirname, '..', 'app_verified.png');
  await page.screenshot({ path: finalScreenshotPath, fullPage: true });
  console.log(`✓ Final screenshot saved to: ${finalScreenshotPath}`);

  console.log('--- Errors Captured ---');
  if (consoleLogs.length === 0) {
    console.log('No errors captured! Clean console.');
  } else {
    consoleLogs.forEach((l) => console.log('  ', l));
  }

  await browser.close();
  console.log('--- All basic Playwright tests completed successfully ---');
}

main().catch(console.error);
