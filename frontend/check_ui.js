import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('Launching browser with channel: msedge...');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', (msg) => {
    console.log(`BROWSER_CONSOLE: [${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', (err) => {
    console.error(`BROWSER_PAGE_ERROR: ${err.toString()}`);
  });

  console.log('Navigating to http://localhost:5180 ...');
  try {
    const response = await page.goto('http://localhost:5180', {
      waitUntil: 'networkidle',
      timeout: 15000,
    });
    console.log(`HTTP Status: ${response.status()}`);
  } catch (err) {
    console.error(`Navigation error: ${err.message}`);
  }

  // Wait 2 seconds for react to render and fetch data
  await page.waitForTimeout(2000);

  // Take screenshot
  const screenshotPath = path.join(__dirname, '..', 'app_screenshot.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved to: ${screenshotPath}`);

  // Get body inner text
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('--- Page Body Text (first 500 chars) ---');
  console.log(bodyText.substring(0, 500));
  console.log('---------------------------------------');

  // Check if root element has children
  const rootChildrenCount = await page.evaluate(() => {
    const root = document.getElementById('root');
    return root ? root.children.length : 0;
  });
  console.log(`Root (#root) children count: ${rootChildrenCount}`);

  await browser.close();
}

main().catch(console.error);
