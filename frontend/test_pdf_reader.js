import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('--- Testing PDF Reader on Double Click ---');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      console.log(`[CONSOLE ERROR] ${msg.text()}`);
    }
  });

  console.log('1. Navigating to http://localhost:5180 ...');
  await page.goto('http://localhost:5180', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Find the imported PDF book card: "Scientific Python Lectures" or book 6
  console.log('2. Locating PDF book card...');
  const pdfCard = page.locator('.glass-card:has-text("Scientific Python Lectures")').first();
  const exists = await pdfCard.count();
  console.log(`PDF Card found: ${exists > 0}`);

  if (exists > 0) {
    console.log('3. Double-clicking on the PDF book card...');
    await pdfCard.dblclick();
    await page.waitForTimeout(2000);

    // Verify we entered ReaderView
    const backBtn = page.locator('button[title="Back to Library"]');
    const isReaderOpen = (await backBtn.count()) > 0;
    console.log(`✓ In Reader View: ${isReaderOpen}`);

    // Verify PDF iframe exists
    const iframe = page.locator('iframe[title="PDF Book Reader"]');
    const iframeCount = await iframe.count();
    console.log(`✓ PDF Reader iframe rendered: ${iframeCount > 0}`);

    if (iframeCount > 0) {
      const src = await iframe.getAttribute('src');
      console.log(`✓ PDF iframe src: ${src}`);
    }

    // Take screenshot of PDF Reader
    const screenshotPath = path.join(__dirname, '..', 'app_pdf_reader_open.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`✓ Screenshot saved to: ${screenshotPath}`);

    // Test going back to library
    console.log('4. Clicking "Back to Library"...');
    await backBtn.click();
    await page.waitForTimeout(1000);
    const inCatalog = (await page.locator('header:has-text("xBookLibrary")').count()) > 0;
    console.log(`✓ Successfully returned to Catalog: ${inCatalog}`);
  } else {
    console.error('Could not find Scientific Python Lectures card');
  }

  await browser.close();
  console.log('--- Test Finished ---');
}

main().catch(console.error);
