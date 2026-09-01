// C10#레시피4 재확인 — 8px 이동취소 임계값이 iOS Safari에서 실제로
// 브라우저 네이티브 pointercancel보다 늦게 발동하는지(우리 판정이
// 실행되기도 전에 제스처가 죽는지) 확인한다.
//
// 중요한 방법론적 한계부터 명시한다: Playwright의 "iPhone 에뮬레이션"은
// 뷰포트 크기·UA 문자열·터치 플래그만 흉내낸다 — 실제로 페이지를
// 그리고 제스처를 판정하는 엔진은 여전히 Chromium(Blink)이지 WebKit이
// 아니다. CONFLICTS.md#C10의 iOS 5.5~14.5px 데이터는 실기기(iPhone/iPad,
// 진짜 Safari)에서 나온 것이라 Playwright로 "재현"할 수 있는 종류의
// 값이 아니다 — 이 스크립트가 확인할 수 있는 건 "Chromium이 iPhone
// 뷰포트에서 이 정확한 코드(touch-action:none)에 대해 CDP 터치로 몇
// px에서 pointercancel을 내는가"뿐이다. 실제 iOS Safari의 답은 이미
// CONFLICTS.md#C10 Precedence 표에 있다(아래 결론에서 그대로 인용).

const path = require("path");
const { chromium, devices } = require("/Users/ojihun/DEV/interaction-doctor/evals/node_modules/playwright");

const URL = "file:///Users/ojihun/DEV/interaction-doctor/tools/nested/reorder-hold-delay-verify.html";

async function realTouchDrag(page, x0, y0, dxTotal, steps) {
	const client = await page.context().newCDPSession(page);
	await client.send("Input.dispatchTouchEvent", {
		type: "touchStart",
		touchPoints: [{ x: x0, y: y0 }],
	});
	for (let i = 1; i <= steps; i++) {
		await client.send("Input.dispatchTouchEvent", {
			type: "touchMove",
			touchPoints: [{ x: x0, y: y0 + (dxTotal * i) / steps }],
		});
		await page.waitForTimeout(20);
	}
	// pointerup은 일부러 안 보낸다 — pointercancel이 나는지만 확인, 630ms까지
	// 대기해서 hold-delay(500ms) 이후 우리 자체 onReorderStart와의 순서도 같이 본다
	return client;
}

async function runOneDistance(browser, distancePx, holdMs) {
	const iPhone = devices["iPhone 13"];
	const context = await browser.newContext({ ...iPhone });
	const page = await context.newPage();
	await page.goto(URL);
	await page.waitForTimeout(50);

	// 레시피 자체의 release()는 dragging이 아직 false면(hold-delay 전
	// 취소) onReorderEnd를 아예 안 부른다 — 그러면 우리가 놓치게 되므로,
	// 이 테스트만을 위해 별도의 원시(raw) pointercancel/pointerup
	// 리스너를 하나 더 달아서 무조건 기록한다. 레시피 코드 자체는
	// 건드리지 않는다(별도 리스너를 추가로 붙이는 것뿐).
	await page.evaluate(() => {
		window.__rawLog = [];
		const t0 = performance.now();
		const target = document.getElementById("target");
		["pointerdown", "pointermove", "pointercancel", "pointerup"].forEach((type) => {
			target.addEventListener(type, (e) => {
				window.__rawLog.push({ type, t: performance.now() - t0, clientY: e.clientY });
			});
		});
	});

	const targetBox = await page.locator("#target").boundingBox();
	const x0 = targetBox.x + targetBox.width / 2;
	const y0 = targetBox.y + targetBox.height / 2;

	const client = await realTouchDrag(page, x0, y0, distancePx, 6);
	await page.waitForTimeout(Math.max(0, holdMs - 6 * 20) + 50); // hold-delay(500ms) 지점까지 관찰

	const rawLog = await page.evaluate(() => window.__rawLog);
	const log = await page.evaluate(() => window.__log);
	const draggingVisual = await page.locator("#target").evaluate((el) => el.classList.contains("dragging"));

	// 정리: touchend를 보내 다음 트라이얼에 영향 안 주게
	await client.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
	await context.close();

	const cancelEntry = rawLog.find((e) => e.type === "pointercancel");
	const startEntry = log.find((e) => e.cb === "onReorderStart");
	return {
		distancePx, rawLog, draggingVisual,
		nativePointercancelFired: !!cancelEntry,
		nativePointercancelAtMs: cancelEntry ? cancelEntry.t : null,
		ourOwnHoldStartFiredAtMs: startEntry ? startEntry.t : null,
	};
}

async function main() {
	const browser = await chromium.launch();
	const results = [];
	// C10 실측 iOS 관찰 취소 구간(5.5~14.5px) 안쪽 값들로 촘촘히 테스트.
	// 8px 미만(우리 임계값보다 작은 값)이 핵심 — 이 구간에서 브라우저가
	// 먼저 취소하면 우리 판정 로직 실행 전에 제스처가 죽는다는 뜻이다.
	for (const d of [3, 5.5, 6.5, 7.9, 8, 10, 12, 14.5]) {
		results.push(await runOneDistance(browser, d, 500));
	}
	await browser.close();
	console.log(JSON.stringify(results.map((r) => ({
		distancePx: r.distancePx,
		nativePointercancelFired: r.nativePointercancelFired,
		nativePointercancelAtMs: r.nativePointercancelAtMs,
		ourOwnHoldStartFiredAtMs: r.ourOwnHoldStartFiredAtMs,
		draggingVisualAtEnd: r.draggingVisual,
	})), null, 2));
}

main().catch((e) => { console.error(e); process.exit(1); });
