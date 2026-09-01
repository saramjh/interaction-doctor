const { chromium } = require("/Users/ojihun/DEV/interaction-doctor/evals/node_modules/playwright");

const URL = "file:///Users/ojihun/DEV/interaction-doctor/tools/nested/swipe-action-verify.html";
const ANDROID_UA = "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36";
const IOS_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.7 Mobile/15E148 Safari/604.1";

async function dragAndRelease(page, dx, dy, { cancel = false, secondPointer = false } = {}) {
	return page.evaluate(async ({ dx, dy, cancel, secondPointer }) => {
		const wait = (ms) => new Promise((r) => setTimeout(r, ms));
		const item = document.getElementById("item");
		if (!item) return { itemGone: true };
		const rect = item.getBoundingClientRect();
		const x0 = rect.left + 20, y0 = rect.top + rect.height / 2;
		const mk = (type, pointerId, x, y) => new PointerEvent(type, { pointerId, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: pointerId === 1, pointerType: "touch" });

		item.dispatchEvent(mk("pointerdown", 1, x0, y0));
		await wait(10);
		if (secondPointer) {
			item.dispatchEvent(mk("pointerdown", 2, x0 + 5, y0 + 5));
			await wait(10);
		}
		// 점진적으로 이동 (중간 스텝 몇 개)
		const steps = 5;
		for (let i = 1; i <= steps; i++) {
			item.dispatchEvent(mk("pointermove", 1, x0 + (dx * i) / steps, y0 + (dy * i) / steps));
			await wait(5);
		}
		if (secondPointer) {
			item.dispatchEvent(mk("pointermove", 2, x0 + 5, y0 + 5)); // 두 번째 포인터는 안 움직임 — 게이트가 무시해야 함
		}
		const transformDuringDrag = item.style.transform;
		if (cancel) {
			item.dispatchEvent(mk("pointercancel", 1, x0 + dx, y0 + dy));
		} else {
			item.dispatchEvent(mk("pointerup", 1, x0 + dx, y0 + dy));
		}
		if (secondPointer) {
			item.dispatchEvent(mk("pointerup", 2, x0 + 5, y0 + 5));
		}
		await wait(10);
		const itemStillThere = !!document.getElementById("item");
		return {
			transformDuringDrag,
			transformAfter: itemStillThere ? document.getElementById("item").style.transform : null,
			commitCount: window.__commitCount,
			itemRemoved: !itemStillThere,
		};
	}, { dx, dy, cancel, secondPointer });
}

async function runCase(browser, { label, userAgent, dx, dy = 0, cancel = false, secondPointer = false }) {
	const context = await browser.newContext({ userAgent, viewport: { width: 400, height: 600 } });
	const page = await context.newPage();
	await page.goto(URL);
	await page.waitForTimeout(30);
	const detectedPlatform = await page.evaluate(() => window.__detectedPlatform);
	const usedThreshold = await page.evaluate(() => window.__usedThreshold);
	const result = await dragAndRelease(page, dx, dy, { cancel, secondPointer });
	await context.close();
	return { label, detectedPlatform, usedThreshold, dx, dy, cancel, secondPointer, ...result };
}

async function main() {
	const browser = await chromium.launch();
	const results = [];

	// 1) 플랫폼 분기: 같은 160px 이동이 Android에서는 커밋되고 iOS에서는 안 되는지
	results.push(await runCase(browser, { label: "android_dx140_belowThreshold(150)", userAgent: ANDROID_UA, dx: -140 }));
	results.push(await runCase(browser, { label: "android_dx160_aboveThreshold(150)", userAgent: ANDROID_UA, dx: -160 }));
	results.push(await runCase(browser, { label: "ios_dx160_belowThreshold(270)", userAgent: IOS_UA, dx: -160 }));
	results.push(await runCase(browser, { label: "ios_dx280_aboveThreshold(270)", userAgent: IOS_UA, dx: -280 }));

	// 2) 수평 의도 게이트: 세로 위주 이동은 절대 커밋 안 됨(Android 기준, 큰 dx라도 dy가 더 크면 무시)
	results.push(await runCase(browser, { label: "verticalDominant_shouldNotCommit", userAgent: ANDROID_UA, dx: -200, dy: -250 }));

	// 3) pointercancel 리셋: 임계값 넘게 이동했어도 취소되면 커밋 안 됨
	results.push(await runCase(browser, { label: "cancelledMidGesture_shouldNotCommit", userAgent: ANDROID_UA, dx: -200, cancel: true }));

	// 4) 멀티포인터 게이트: 두 번째 포인터가 끼어들어도 첫 포인터 기준으로 정상 커밋
	results.push(await runCase(browser, { label: "secondPointerInterferes_shouldStillCommitOnPointer1", userAgent: ANDROID_UA, dx: -160, secondPointer: true }));

	console.log(JSON.stringify(results, null, 2));
	await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
