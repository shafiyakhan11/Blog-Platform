import { test, expect } from '@playwright/test';

test.use({ channel: 'msedge' });

test('signup-screen', async ({ page }) => {
  await page.route("**/*", async route => {
    const requestUrl = new URL(route.request().url());
    if (requestUrl.origin === "http://127.0.0.1:5173") {
      await route.continue();
    } else {
      await route.abort("blockedbyclient");
    }
  });
  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button', { name: 'Sign up' }).click();
  await expect(page.getByRole('heading', { name: 'Create your account' })).toHaveText("Create your account");
});
