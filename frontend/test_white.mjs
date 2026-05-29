import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

const errors = [];
page.on('pageerror', err => errors.push(err.message));
page.on('console', msg => {
  if (msg.type() === 'error') errors.push('CONSOLE ERROR: ' + msg.text());
});

await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
console.log('Dashboard loaded, errors so far:', errors.length);

// Click IP History
await page.click('text=IP 历史');
await page.waitForTimeout(2000);
console.log('After clicking IP History, errors:', errors);
console.log('Page content visible:', await page.locator('.el-main').isVisible());

// Click Dashboard
await page.click('text=仪表盘');
await page.waitForTimeout(2000);
console.log('After clicking Dashboard, errors:', errors);
console.log('Page content visible:', await page.locator('.el-main').isVisible());

// Check if the employee dropdown has options on History page
await page.click('text=IP 历史');
await page.waitForTimeout(1000);
const options = await page.locator('.el-select-dropdown__item').count();
console.log('Employee dropdown options count:', options);

await browser.close();
