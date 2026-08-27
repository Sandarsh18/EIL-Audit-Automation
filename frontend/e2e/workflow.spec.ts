import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

test('End-to-End Excel Audit Workflow', async ({ page }) => {
  test.setTimeout(120000);
  
  // Resolve fixture paths (Playwright runs from frontend dir)
  const e1Path = path.resolve('../backend/tests/fixtures/real_e1.xlsx');
  const e2Path = path.resolve('../backend/tests/fixtures/CONSOLIDATED ManhourAp25.xlsx');
  const e3Path = path.resolve('../backend/tests/fixtures/CONSOLIDATED ManhourAp25.xlsx');
  
  if (!fs.existsSync(e1Path) || !fs.existsSync(e2Path) || !fs.existsSync(e3Path)) {
    test.skip('Test fixtures missing, skipping E2E test.');
    return;
  }

  // Capture console/error/network for debugging
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  page.on('pageerror', exception => console.log(`PAGE ERROR: "${exception}"`));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));

  await page.goto('/');

  // ═══════════════════════════════════════════════
  // STEP 1: Upload Source Workbooks
  // ═══════════════════════════════════════════════
  await expect(page.getByText('Step 1: Upload Source Workbooks')).toBeVisible();
  
  const e1Input = page.locator('label').filter({ hasText: 'Click to upload excel1' }).locator('input[type="file"]');
  const e2Input = page.locator('label').filter({ hasText: 'Click to upload excel2' }).locator('input[type="file"]');
  const e3Input = page.locator('label').filter({ hasText: 'Click to upload excel3' }).locator('input[type="file"]');

  await e1Input.setInputFiles(e1Path);
  await expect(page.locator('div').filter({ hasText: '[ Excel 1 ] CONSOLIDATED REPORT' }).getByText('Uploaded', { exact: true }).first()).toBeVisible();

  await e2Input.setInputFiles(e2Path);
  await expect(page.locator('div').filter({ hasText: '[ Excel 2 ] INSPECTION CALL LOG' }).getByText('Uploaded', { exact: true }).first()).toBeVisible();

  await e3Input.setInputFiles(e3Path);
  await expect(page.locator('div').filter({ hasText: '[ Excel 3 ] MASTER TEMPLATE' }).getByText('Uploaded', { exact: true }).first()).toBeVisible();

  // Proceed to Step 2
  await page.getByRole('button', { name: 'Proceed to Mapping →' }).click();

  // ═══════════════════════════════════════════════
  // STEP 2: Inspect & Map Columns
  // ═══════════════════════════════════════════════
  await expect(page.getByText('Step 2: Inspect & Map Columns')).toBeVisible();
  
  // Wait for data to load (populates select options)
  await page.waitForTimeout(2000);
  
  // Excel 1 mapping
  await page.locator('select[name="job_number"]').nth(0).selectOption('Job No.');
  await page.locator('select[name="balance_quantity"]').nth(0).selectOption('Balance Quantity');
  await page.locator('select[name="ocs_date"]').nth(0).selectOption('OCS Date');
  
  // Excel 2 mapping
  await page.locator('select[name="job_number"]').nth(1).selectOption('Job No.');
  await page.locator('select[name="inspection_from"]').nth(0).selectOption('Inspection Attended (From)');
  await page.locator('select[name="inspection_upto"]').nth(0).selectOption('Inspection Attended (Upto)');
  await page.locator('select[name="date_received"]').nth(0).selectOption('Date Received');

  // Excel 3 mapping (Auto-mapped mostly, but we trigger the select if needed, or just let auto-map work)
  // Instead of hardcoding, we wait for the auto-mapping to complete or select the first available option
  await page.waitForTimeout(2000); // Give auto-map time
  // Select any missing required fields by picking the second option (index 1) since index 0 is "-- Select --"
  const excel3Selects = ['job_number', 'running_orders', 'orders_for_fd', 'ocs_done', 'expediting', 'inspection', 'others', 'total'];
  for (const field of excel3Selects) {
      const loc = page.locator(`select[name="${field}"]`).first();
      if (await loc.isVisible()) {
          const val = await loc.inputValue();
          if (!val) {
              await loc.selectOption({ index: 1 });
          }
      }
  }

  await page.getByRole('button', { name: 'Validate and Proceed' }).click();
  
  // Should auto-transition to Step 3
  await expect(page.getByText('Step 3: Select Jobs')).toBeVisible({ timeout: 15000 });
  
  // ═══════════════════════════════════════════════
  // STEP 3: Select Jobs — Use Select All (real workflow)
  // ═══════════════════════════════════════════════
  await page.getByRole('button', { name: 'Select All' }).click();
  await page.getByRole('button', { name: 'View Matching Records' }).click();

  // ═══════════════════════════════════════════════
  // STEP 4: Rule Analysis
  // ═══════════════════════════════════════════════
  await expect(page.getByText('Step 4: Rule Analysis')).toBeVisible({ timeout: 15000 });
  await page.getByRole('button', { name: 'Proceed to Review →' }).click();

  // ═══════════════════════════════════════════════
  // STEP 5: Review & Approve — Target B269 only
  // ═══════════════════════════════════════════════
  // Verify Step 5 is active
  await expect(page.getByText('Step 5: Review & Approve')).toBeVisible({ timeout: 15000 });
  
  // Wait for review data to load (review table renders after API call)
  await expect(page.locator('[data-test-id="job-row-b269"]')).toBeVisible({ timeout: 15000 });
  
  // Click Review to expand B269 detail panel (required before approve button appears)
  const reviewBtn = page.locator('[data-test-id="review-b269"]');
  await expect(reviewBtn).toBeVisible();
  await reviewBtn.click();
  
  // Verify approve button appears in expanded detail panel
  const approveBtn = page.locator('[data-test-id="approve-b269"]');
  await expect(approveBtn).toBeVisible({ timeout: 5000 });
  await approveBtn.click();
  
  // Wait for approval to process — verify B269 row shows APPROVED status
  await expect(
    page.locator('[data-test-id="job-row-b269"]').getByText('APPROVED', { exact: true })
  ).toBeVisible({ timeout: 10000 });
  
  // Verify the Proceed button is now enabled (was disabled with 0 approved)
  const proceedBtn = page.getByRole('button', { name: /Proceed to Output Generation/ });
  await expect(proceedBtn).toBeEnabled({ timeout: 5000 });
  
  // Proceed to Output
  await proceedBtn.click();

  // ═══════════════════════════════════════════════
  // STEP 6: Output Generation
  // ═══════════════════════════════════════════════
  await expect(page.getByText('Step 6: Generate Output')).toBeVisible({ timeout: 15000 });
  await expect(page.getByText('OUTPUT GENERATION')).toBeVisible({ timeout: 15000 });
  
  // If there are formula overwrite checkboxes, approve them through the real UI
  const checkboxes = await page.locator('input[type="checkbox"][title="Approve formula overwrite"]').all();
  for (const cb of checkboxes) {
    await cb.check();
  }
  
  // Generate the output
  await page.getByRole('button', { name: 'Generate Excel 3' }).click();

  // Wait for output generation + validation to complete
  await expect(page.getByText('Verified')).toBeVisible({ timeout: 30000 });
  
  // Verify the success state
  await expect(page.getByText('Output Generated Successfully')).toBeVisible();
  
  // ═══════════════════════════════════════════════
  // STEP 7: Download & Validate
  // ═══════════════════════════════════════════════
  const downloadBtn = page.locator('[data-test-id="download-output"]');
  await expect(downloadBtn).toBeVisible();
  
  const downloadPromise = page.waitForEvent('download');
  await downloadBtn.click();
  const download = await downloadPromise;
  
  // Verify filename
  expect(download.suggestedFilename()).toBe('CONSOLIDATED_Manhour_Automated.xlsx');
  
  // Save the downloaded file and verify it physically exists
  const downloadPath = path.resolve('../test-results/downloaded_output.xlsx');
  await download.saveAs(downloadPath);
  expect(fs.existsSync(downloadPath)).toBe(true);
  
  // Verify file size is reasonable (not empty/corrupt)
  const stats = fs.statSync(downloadPath);
  expect(stats.size).toBeGreaterThan(10000); // Real workbook should be > 10KB
});
