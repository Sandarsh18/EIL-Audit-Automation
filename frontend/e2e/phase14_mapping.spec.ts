import { test, expect } from '@playwright/test';
import * as path from 'path';

test.describe('Phase 14: Dynamic Excel 3 Sheet Selection', () => {
  test('should allow changing sheets and clearing incompatible mappings', async ({ page }) => {
    // 1. Upload files
    await page.goto('/');
    
    // Set up mock inputs
    const b378TestDir = path.resolve('/home/1RV24MC093_SANDARSH_J_N/projects/eil1/local_test_data');
    const fixturesDir = path.resolve('/home/1RV24MC093_SANDARSH_J_N/projects/eil1/backend/tests/fixtures');
    const excel1Path = path.join(fixturesDir, 'real_e1.xlsx');
    const excel2Path = path.join(fixturesDir, 'real_e2.xlsx');
    const excel3Path = path.join(b378TestDir, 'CONSOLIDATED ManhourAp25.xlsx');
    
    await page.locator('input[type="file"]').nth(0).setInputFiles(excel1Path);
    await page.waitForTimeout(500);
    await page.locator('input[type="file"]').nth(1).setInputFiles(excel2Path);
    await page.waitForTimeout(500);
    await page.locator('input[type="file"]').nth(2).setInputFiles(excel3Path);
    
    // Wait for uploads to complete
    await expect(page.locator('text=Uploaded').first()).toBeVisible({ timeout: 10000 });
    
    // Proceed to Step 2
    await page.getByRole('button', { name: 'Proceed to Mapping →' }).click();

    // Wait for the mapping config UI to appear
    await page.waitForSelector('text=Configure Column Mapping', { timeout: 15000 });
    
    // 2. Verify Default Selection is Mar26
    const sheet3Select = page.locator('select').nth(2);
    await expect(sheet3Select).toHaveValue('ConsolidatedMHrequirementMar26');
    
    // 3. Verify Mar26 schema (Modern - has OCS Done)
    await expect(page.locator('text=Rows').first()).toBeVisible();
    await expect(page.locator('text=modern').first()).toBeVisible();
    
    // Check if modern fields are mapped
    const ocsDoneSelect = page.locator('select[name="ocs_done"]');
    await expect(ocsDoneSelect).toHaveValue('OCS done');
    
    // 4. Change Sheet to Apr25
    await sheet3Select.selectOption('ConsolidatedMHrequirementApr25');
    
    // 5. Warning Dialog Appears
    const dialog = page.locator('text=Change Source Sheet?');
    await expect(dialog).toBeVisible();
    
    // Cancel first
    await page.locator('button:has-text("Cancel")').click();
    await expect(dialog).not.toBeVisible();
    await expect(sheet3Select).toHaveValue('ConsolidatedMHrequirementMar26'); // Reverts to Mar26
    
    // Change and confirm
    await sheet3Select.selectOption('ConsolidatedMHrequirementApr25');
    await page.locator('button:has-text("Change Sheet")').click();
    
    // Wait for schema reload
    await page.waitForTimeout(1000);
    await expect(sheet3Select).toHaveValue('ConsolidatedMHrequirementApr25');
    await expect(page.locator('text=legacy').first()).toBeVisible();
    
    // 6. Check that modern fields are NOT available in Apr25
    await expect(page.locator('text=NOT AVAILABLE IN SELECTED SHEET').first()).toBeVisible();
    
    // 7. Validate Mapping and check calculation
    await page.click('button:has-text("Validate and Proceed")');
    await page.waitForSelector('text=Match Preview', { state: 'visible', timeout: 10000 });
    
    // Ensure B378 is present
    await expect(page.locator('text=B378').first()).toBeVisible();
    
    // Proceed to matching
    await page.click('button:has-text("Confirm & Proceed")');
    
    // Go to calculations
    await page.waitForSelector('text=Run Evaluation');
    await page.click('button:has-text("Run Evaluation")');
    
    // Validate that evidence Lineage is displayed in the calculation results
    await page.waitForSelector('text=Evidence', { state: 'visible', timeout: 10000 });
    await page.click('button:has-text("View")'); // expand
    
    await expect(page.locator('text=Calculation Evidence')).toBeVisible();
    await expect(page.locator('text=Excel 3 Source Lineage')).toBeVisible();
    await expect(page.locator('text=ConsolidatedMHrequirementApr25').first()).toBeVisible();
  });
});
