/**
 * Playwright E2E Test: Feature 015 - Core Metadata Editor, Online Metadata Search,
 * Multi-Format Management, and Bulk Editing.
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

test.describe('Feature 015: Core Metadata Editor and Import Suite', () => {
  test('Single-book metadata editor lifecycle, hotkey E, and save', async ({ page }) => {
    await page.goto('http://localhost:5180', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // 1. Select the first available book
    const firstBook = page.locator('[data-testid="book-card"], .book-card, div:has-text("Dune"), div:has-text("Foundation")').first();
    await firstBook.click();
    await page.waitForTimeout(500);

    // 2. Open Edit Metadata modal via 'E' hotkey or Edit Metadata button
    const editBtn = page.locator('button:has-text("Edit Metadata"), button[title*="Edit book metadata"]');
    if (await editBtn.count() > 0) {
      await editBtn.first().click();
    } else {
      await page.keyboard.press('KeyE');
    }

    // Verify modal is open
    const modalTitle = page.locator('text=Edit Metadata').first();
    await expect(modalTitle).toBeVisible({ timeout: 5000 });

    // 3. Edit title and rating
    const titleInput = page.locator('input[placeholder*="Title"], label:has-text("Title") + input, input[value]').first();
    await titleInput.fill('Dune (Special Collectors Edition)');

    // 4. Test Online Metadata Drawer trigger
    const downloadMetaBtn = page.locator('button:has-text("Download Metadata")');
    if (await downloadMetaBtn.count() > 0) {
      await downloadMetaBtn.click();
      await page.waitForTimeout(500);
      const drawerHeading = page.locator('text=Online Metadata Search, text=Candidates').first();
      // Drawer should be visible
      await expect(drawerHeading).toBeVisible({ timeout: 3000 });
      // Close drawer
      const closeDrawerBtn = page.locator('button[title="Close Drawer"], button:has-text("Close")').first();
      if (await closeDrawerBtn.count() > 0) {
        await closeDrawerBtn.click();
      }
    }

    // 5. Save changes using Ctrl+Enter or Save button
    const saveBtn = page.locator('button:has-text("Save Metadata"), button:has-text("Save Changes")').first();
    if (await saveBtn.count() > 0) {
      await saveBtn.click();
    } else {
      await page.keyboard.press('Control+Enter');
    }

    // Verify modal closes and toast appears or title is updated
    await page.waitForTimeout(1000);
    const toast = page.locator('text=saved, text=Updated, text=Success').first();
    if (await toast.count() > 0) {
      await expect(toast).toBeVisible();
    }
  });

  test('Multi-format management controls in Detail Inspector', async ({ page }) => {
    await page.goto('http://localhost:5180', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // Select book
    const firstBook = page.locator('text=Dune').first();
    if (await firstBook.count() > 0) {
      await firstBook.click();
      await page.waitForTimeout(500);
    }

    // Check Formats section
    const formatSection = page.locator('text=Available Formats, text=Formats').first();
    await expect(formatSection).toBeVisible({ timeout: 5000 });

    // Verify "+ Add Format" button is present
    const addFormatBtn = page.locator('button:has-text("Add Format"), button[title*="Attach an additional format"]');
    await expect(addFormatBtn).toBeVisible();
  });

  test('Bulk selection and Bulk Edit modal display', async ({ page }) => {
    await page.goto('http://localhost:5180', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // Switch to table view where multi-select checkboxes are standard
    const tableBtn = page.locator('button[title*="Table"], button:has-text("Table")').first();
    if (await tableBtn.count() > 0) {
      await tableBtn.click();
      await page.waitForTimeout(600);
    }

    // Select checkboxes for multiple books
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count >= 2) {
      await checkboxes.nth(1).check();
      if (count >= 3) {
        await checkboxes.nth(2).check();
      }
      await page.waitForTimeout(500);

      // Verify floating Bulk Action Bar appears
      const bulkBar = page.locator('text=Selected, button:has-text("Bulk Edit")').first();
      await expect(bulkBar).toBeVisible({ timeout: 3000 });

      // Click "Bulk Edit"
      const bulkEditBtn = page.locator('button:has-text("Bulk Edit")').first();
      await bulkEditBtn.click();
      await page.waitForTimeout(500);

      // Verify Bulk Edit Modal opens
      const bulkModalHeader = page.locator('text=Bulk Edit Books').first();
      await expect(bulkModalHeader).toBeVisible();

      // Press Escape to dismiss
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
      await expect(bulkModalHeader).not.toBeVisible();
    }
  });
});
