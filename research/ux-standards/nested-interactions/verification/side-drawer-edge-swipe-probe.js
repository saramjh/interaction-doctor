const { chromium, devices } = require("playwright");

async function tryEdgeSwipeBack(page, label) {
	const client = await page.context().newCDPSession(page);
	const viewport = page.viewportSize();
	const y = Math.round(viewport.height / 2);

	// Touch sequence starting at the very left edge (x=1) moving right,
	// which is the physical gesture that a real mobile browser interprets
	// as "swipe from edge to go back". Dispatched via CDP Input domain,
	// the same primitive Playwright's own touchscreen.tap() uses, since
	// Playwright's public touchscreen API has no move/swipe method.
	const points = [];
	for (let x = 1; x <= 220; x += 8) {
		points.push({ x, y });
	}

	try {
		await client.send("Input.dispatchTouchEvent", {
			type: "touchStart",
			touchPoints: [{ x: points[0].x, y: points[0].y }],
		});
		for (let i = 1; i < points.length; i++) {
			await client.send("Input.dispatchTouchEvent", {
				type: "touchMove",
				touchPoints: [{ x: points[i].x, y: points[i].y }],
			});
			await page.waitForTimeout(8);
		}
		await client.send("Input.dispatchTouchEvent", {
			type: "touchEnd",
			touchPoints: [],
		});
		return { ok: true, label };
	} catch (err) {
		return { ok: false, label, error: String(err) };
	}
}

(async () => {
	const results = {};

	for (const headless of [true, false]) {
		const browser = await chromium.launch({ headless });
		for (const pageFile of ["page2.html", "page2-contained.html"]) {
			const context = await browser.newContext({
				...devices["iPhone 13"],
			});
			const page = await context.newPage();

			await page.goto("http://localhost:8935/page1.html");
			await page.goto("http://localhost:8935/" + pageFile);
			const urlBefore = page.url();
			const titleBefore = await page.title();

			const dispatchResult = await tryEdgeSwipeBack(page, pageFile + " headless=" + headless);

			await page.waitForTimeout(300);
			const urlAfter = page.url();
			const titleAfter = await page.title();

			const key = pageFile.replace(".html", "") + "_headless_" + headless;
			results[key] = {
				dispatchResult,
				urlBefore,
				urlAfter,
				titleBefore,
				titleAfter,
				navigatedBack: urlAfter !== urlBefore,
			};

			await context.close();
		}
		await browser.close();
	}

	console.log(JSON.stringify(results, null, 2));
})();
