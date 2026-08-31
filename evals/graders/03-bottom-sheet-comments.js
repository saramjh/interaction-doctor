// 채점 기준: nested-interactions/bottom-sheet-scroll-drag.md §5 런타임
// 검증 조건(§4.5 규칙 1 포함) 그대로 — 원본 §5-0이 재현한 두 가지:
//   - 규칙 1: pointerdown 없이 pointermove만 와도 시트가 움직이면 안 됨
//   - scrollTop 기준 소유권: 리스트가 맨 위가 아니면(scrollTop>0) 드래그해도
//     시트는 절대 반응하지 않아야 하고(콘텐츠 스크롤이 이긴다),
//     맨 위(scrollTop=0)에서 아래로 당길 때만 시트가 움직여야 한다.
// 규칙 2(멀티포인터)는 원본 문서 자체가 "해당 없음"으로 판정해뒀다
// (단일 포인터 가정이 합리적인 시나리오) — 여기서도 별도로 강제하지
// 않는다.
//
// 먼저 스크립트가 애초에 정상 실행되는지(댓글 40개가 실제로 렌더됐는지)
// 부터 확인한다 — 실행 자체가 안 되면 나머지 항목은 전부 "실행 불가"로
// 기록한다.

const { runScenarioFresh } = require("./_lib");

async function scriptRanAtAll(page) {
	const count = await page.evaluate(() => document.querySelectorAll(".comment").length);
	return count === 40;
}

const subtests = {
	async scriptExecutes(page) {
		const commentCount = await page.evaluate(() => document.querySelectorAll(".comment").length);
		return { commentCount, expected: 40, scriptRanAtAll: commentCount === 40 };
	},

	async rule1_bareMoveOnHandle(page) {
		if (!(await scriptRanAtAll(page))) return { skipped: "script did not execute" };
		const before = await page.evaluate(() => document.getElementById("sheet").style.transform);
		await page.evaluate(() => {
			const sheet = document.getElementById("sheet");
			const rect = sheet.getBoundingClientRect();
			sheet.dispatchEvent(new PointerEvent("pointermove", { pointerId: 1, clientX: rect.left + rect.width / 2, clientY: rect.top + 100, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" }));
		});
		const after = await page.evaluate(() => document.getElementById("sheet").style.transform);
		return { transformBefore: before, transformAfterBareMove: after, reactedWithoutPointerdown: before !== after };
	},

	// scrollTop > 0(맨 위 아님)일 때 콘텐츠를 드래그해도 시트는 절대 안 움직여야 함
	async scrollTopGtZero_sheetMustNotMove(page) {
		if (!(await scriptRanAtAll(page))) return { skipped: "script did not execute" };
		await page.evaluate(() => { document.getElementById("comments").scrollTop = 300; });
		const scrollTopBefore = await page.evaluate(() => document.getElementById("comments").scrollTop);
		const transformBefore = await page.evaluate(() => document.getElementById("sheet").style.transform);

		await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const sheet = document.getElementById("sheet");
			const comments = document.getElementById("comments");
			const rect = comments.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y0 = rect.top + 40;
			const mk = (type, dy) => new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y0 + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			// 댓글 목록(맨 위 아님) 위에서 아래로 200px 드래그 시도
			comments.dispatchEvent(mk("pointerdown", 0));
			await wait(20);
			comments.dispatchEvent(mk("pointermove", 200));
			await wait(20);
			comments.dispatchEvent(mk("pointerup", 200));
			await wait(20);
		});

		const transformAfter = await page.evaluate(() => document.getElementById("sheet").style.transform);
		return {
			scrollTopBefore,
			transformBefore,
			transformAfter,
			sheetStayedStill: transformBefore === transformAfter || transformAfter === "" || transformAfter === "translateY(0px)",
		};
	},

	// scrollTop === 0(맨 위)일 때 아래로 당기면 시트가 실제로 움직여야 함
	async scrollTopZero_sheetShouldMove(page) {
		if (!(await scriptRanAtAll(page))) return { skipped: "script did not execute" };
		const scrollTopBefore = await page.evaluate(() => document.getElementById("comments").scrollTop);

		await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const sheet = document.getElementById("sheet");
			const comments = document.getElementById("comments");
			const rect = comments.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y0 = rect.top + 40;
			const mk = (type, dy) => new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y0 + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			comments.dispatchEvent(mk("pointerdown", 0));
			await wait(20);
			comments.dispatchEvent(mk("pointermove", 200));
			await wait(20);
		});

		const transformDuring = await page.evaluate(() => document.getElementById("sheet").style.transform);
		return {
			scrollTopBeforeIsZero: scrollTopBefore === 0,
			transformDuring,
			sheetMoved: transformDuring !== "" && transformDuring !== "translateY(0px)",
		};
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 03-bottom-sheet-comments.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "03-bottom-sheet-comments", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
