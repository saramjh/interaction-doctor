const { chromium } = require("playwright");
(async () => {
  const results = {};
  for (const pageFile of ["page2.html", "page2-contained.html"]) {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ viewport: { width: 800, height: 600 } });
    const page = await context.newPage();
    await page.goto("http://localhost:8935/page1.html");
    await page.goto("http://localhost:8935/" + pageFile);
    const urlBefore = page.url();

    // Desktop trackpad-style horizontal overscroll swipe-to-navigate:
    // repeated wheel events with a large negative deltaX (content already
    // at its horizontal scroll boundary, since these pages don't scroll).
    for (let i = 0; i < 40; i++) {
      await page.mouse.wheel(-120, 0);
      await page.waitForTimeout(5);
    }
    await page.waitForTimeout(400);
    const urlAfter = page.url();
    results[pageFile] = { urlBefore, urlAfter, navigatedBack: urlAfter !== urlBefore };
    await browser.close();
  }
  console.log(JSON.stringify(results, null, 2));
})();
