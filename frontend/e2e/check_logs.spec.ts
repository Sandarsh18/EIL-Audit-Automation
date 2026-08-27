import { test } from '@playwright/test';
import * as path from 'path';

test('check console', async ({ page }) => {
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    await page.goto('/');
    const b378TestDir = path.resolve('/home/1RV24MC093_SANDARSH_J_N/projects/eil1/local_test_data');
    const fixturesDir = path.resolve('/home/1RV24MC093_SANDARSH_J_N/projects/eil1/backend/tests/fixtures');
    
    await page.locator('input[type="file"]').nth(0).setInputFiles(path.join(fixturesDir, 'real_e1.xlsx'));
    await page.waitForTimeout(500);
    await page.locator('input[type="file"]').nth(1).setInputFiles(path.join(fixturesDir, 'real_e2.xlsx'));
    await page.waitForTimeout(500);
    await page.locator('input[type="file"]').nth(2).setInputFiles(path.join(b378TestDir, 'CONSOLIDATED ManhourAp25.xlsx'));
    await page.waitForTimeout(2000);
});
