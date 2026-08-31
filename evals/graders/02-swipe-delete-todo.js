// 채점 기준: common-pitfalls.md §4.5 규칙 1(pointerdown 미확인)·규칙
// 2(멀티포인터) — 이 시나리오의 원본 결함이 정확히 규칙 1이었다.
// 보조로 research/ux-standards/patterns/swipe-actions.md의 [표준]
// 커밋 거리(Android `getSwipeThreshold()` 기본값 50%, 항목 폭 기준)를
// 실제 구현이 어떤 값을 쓰는지 관찰만 한다(이 시나리오가 애초에
// 재현하려던 결함은 아니라서 별도 pass/fail을 매기지 않는다).

const { runScenarioFresh } = require("./_lib");

const subtests = {
	// 규칙 1: pointerdown 없이 pointermove/pointerup만 왔을 때 반응하면 안 됨
	async rule1_bareMove(page) {
		const item = page.locator(".item").first();
		const box = await item.boundingBox();
		const before = await item.evaluate((el) => el.style.transform);
		await page.evaluate(({ x, y }) => {
			const item = document.querySelectorAll(".item")[0];
			item.dispatchEvent(new PointerEvent("pointermove", { pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" }));
		}, { x: box.x + box.width - 5, y: box.y + box.height / 2 }); // 오른쪽 끝 근처(가장 dx가 커지기 쉬운 지점)
		const after = await item.evaluate((el) => el.style.transform);
		return { transformBefore: before, transformAfterBareMove: after, reactedWithoutPointerdown: before !== after };
	},

	async rule1_bareUpDeletes(page) {
		const before = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		const box = await page.locator(".item").first().boundingBox();
		await page.evaluate(({ x, y }) => {
			const item = document.querySelectorAll(".item")[0];
			item.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" }));
		}, { x: box.x + box.width - 5, y: box.y + box.height / 2 });
		const after = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		return { countBefore: before.length, countAfter: after.length, deletedWithoutPointerdown: after.length < before.length, before, after };
	},

	// 정상 스와이프(진짜 pointerdown부터)는 여전히 되는지 — 규칙 1을 고치면서
	// 정상 동작까지 같이 깨뜨리지 않았는지 확인
	async normalSwipeStillWorks(page) {
		const before = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		const box = await page.locator(".item").first().boundingBox();
		const y = box.y + box.height / 2;
		await page.evaluate(async ({ x0, y }) => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const item = document.querySelectorAll(".item")[0];
			const mk = (type, x) => new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			item.dispatchEvent(mk("pointerdown", x0));
			await wait(20);
			item.dispatchEvent(mk("pointermove", x0 - 100));
			await wait(20);
			item.dispatchEvent(mk("pointerup", x0 - 100));
			await wait(20);
		}, { x0: box.x + box.width - 5, y });
		const after = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		return { deletedByRealSwipe: after.length === before.length - 1 && before[0] === "우유 사기" && after[0] !== "우유 사기" };
	},

	// 규칙 2: 같은 항목에 두 번째 포인터가 끼어듦. pointerId=2를 pointerId=1이
	// "끝날 지점" 바로 근처에서 누르게 해서, startX가 덮어써지면(=상태
	// 미격리) 최종 dx가 임계값(80px) 밑으로 떨어져 "삭제 안 됨"으로,
	// 격리돼 있으면 "삭제됨"으로 — 결과가 갈리게 설계한다.
	async rule2_secondPointer(page) {
		const before = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		const box = await page.locator(".item").first().boundingBox();
		const y = box.y + box.height / 2;
		const rightEdgeX = box.x + box.width - 5;
		const endX = rightEdgeX - 90; // pointerId=1이 실제로 도착할 지점 (dx=-90, 임계값 -80 넘음)
		const phantomX = endX + 5; // pointerId=2가 그 근처를 누름 — 덮어써지면 dx가 -5로 쪼그라듦
		await page.evaluate(async ({ rightEdgeX, y, endX, phantomX }) => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const item = document.querySelectorAll(".item")[0];
			const mk = (type, pointerId, x) => new PointerEvent(type, { pointerId, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: pointerId === 1, pointerType: "touch" });

			// pointerId=1: 오른쪽 끝에서 시작해 왼쪽으로 90px 밀려는 진짜 삭제 제스처
			item.dispatchEvent(mk("pointerdown", 1, rightEdgeX));
			await wait(200);
			// pointerId=2: 같은 항목의 다른 지점에 다른 손가락이 닿음(첫 번째 해제 안 함)
			item.dispatchEvent(mk("pointerdown", 2, phantomX));
			await wait(50);

			item.dispatchEvent(mk("pointermove", 1, endX));
			await wait(20);
			item.dispatchEvent(mk("pointerup", 1, endX));
			await wait(20);
			item.dispatchEvent(mk("pointerup", 2, phantomX));
			await wait(20);
		}, { rightEdgeX, y, endX, phantomX });
		const after = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		return { deletedAsIntended: after.length === before.length - 1 && before[0] === "우유 사기" && after[0] !== "우유 사기", before, after };
	},

	// 참고용 관찰(합/불 판정 아님): 커밋 거리가 항목 폭 기준 50%인지, 고정 px인지
	async observeCommitThreshold(page) {
		const box = await page.locator(".item").first().boundingBox();
		const half = box.width / 2;
		const before = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		await page.evaluate(async ({ x0, y, dx }) => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const item = document.querySelectorAll(".item")[0];
			const mk = (type, x) => new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			item.dispatchEvent(mk("pointerdown", x0));
			await wait(20);
			item.dispatchEvent(mk("pointermove", x0 - dx));
			await wait(20);
			item.dispatchEvent(mk("pointerup", x0 - dx));
			await wait(20);
		}, { x0: box.x + box.width - 5, y: box.y + box.height / 2, dx: half - 5 }); // 항목 폭의 정확히 50% 살짝 못 미치게
		const after = await page.$$eval(".label", (els) => els.map((e) => e.textContent));
		return {
			itemWidthPx: Math.round(box.width),
			movedPx: Math.round(half - 5),
			movedFractionOfWidth: Number(((half - 5) / box.width).toFixed(2)),
			deletedAtJustUnder50pctWidth: after.length < before.length,
		};
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 02-swipe-delete-todo.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "02-swipe-delete-todo", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
