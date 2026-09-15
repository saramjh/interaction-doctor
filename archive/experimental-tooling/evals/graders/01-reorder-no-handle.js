// 채점 기준: skills/interaction-doctor/references/recipes.md 레시피 4(a~d)를
// 그대로 가져온다 + common-pitfalls.md 규칙 1·2.
//
//   a. 8px 미만 이동 유지 → 재정렬(드래그) 모드 진입, 정확한 ms 기록
//   b. 지연 메커니즘 도중 8px 넘게 이동 → 진입 취소 (지연 메커니즘이
//      없는 구현은 "해당 없음"으로 기록한다 — 억지로 pass/fail 매기지 않는다)
//   c. 진입 후 이동 → 실제로 재정렬(렌더된 DOM 순서 변화로 확인)
//   d. 두 번째 포인터가 같은 행에 끼어듦 → common-pitfalls 규칙 2:
//      상태가 격리되는지, 아니면 레시피 1이 실패했던 것처럼 공유 변수가
//      덮어써지는지
//
// 코드를 읽고 "있다/없다" 판단하지 않는다 — 실제로 합성 PointerEvent를
// 던져서 DOM에 실제로 반영된 결과(클래스, transform, 렌더된 텍스트 순서)로만
// 판정한다. a~d는 서로 오염되지 않도록 매번 새 페이지 로드에서 실행한다.

const { runScenarioFresh } = require("./_lib");

async function titles(page) {
	return page.$$eval(".title", (els) => els.map((e) => e.textContent));
}

async function rowHeightOf(page) {
	return page.evaluate(() => {
		const rows = document.querySelectorAll(".track");
		const r0 = rows[0].getBoundingClientRect();
		const r1 = rows[1] ? rows[1].getBoundingClientRect() : null;
		return r1 ? r1.top - r0.top : r0.height + 6;
	});
}

const subtests = {
	async a(page) {
		const before = await titles(page);
		const r = await page.evaluate(async () => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const row = document.querySelectorAll(".track")[0];
			const rect = row.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y = rect.top + rect.height / 2;
			const mk = (type, dy) =>
				new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });

			const t0 = performance.now();
			let enteredAtMs = null;
			const obs = new MutationObserver(() => {
				if (enteredAtMs == null && row.classList.contains("dragging")) enteredAtMs = performance.now() - t0;
			});
			obs.observe(row, { attributes: true, attributeFilter: ["class"] });

			row.dispatchEvent(mk("pointerdown"));
			await wait(50);
			row.dispatchEvent(mk("pointermove", 3)); // < 8px
			await wait(650);
			obs.disconnect();
			const draggingAtEnd = row.classList.contains("dragging");
			row.dispatchEvent(mk("pointerup", 3));
			await wait(30);
			return { enteredAtMs, draggingAtEnd };
		});
		return { ...r, titlesUnaffected: JSON.stringify(before) === JSON.stringify(await titles(page)) };
	},

	async b(page) {
		const before = await titles(page);
		const r = await page.evaluate(async () => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const row = document.querySelectorAll(".track")[0];
			const rect = row.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y = rect.top + rect.height / 2;
			const mk = (type, dy) =>
				new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });

			const t0 = performance.now();
			let enteredAtMs = null;
			const obs = new MutationObserver(() => {
				if (enteredAtMs == null && row.classList.contains("dragging")) enteredAtMs = performance.now() - t0;
			});
			obs.observe(row, { attributes: true, attributeFilter: ["class"] });

			row.dispatchEvent(mk("pointerdown"));
			await wait(60);
			row.dispatchEvent(mk("pointermove", 40)); // 40px > 8px, 대부분의 지연(<=500ms)보다 훨씬 전
			await wait(650);
			obs.disconnect();
			const draggingAtEnd = row.classList.contains("dragging");
			row.dispatchEvent(mk("pointerup", 40));
			await wait(30);
			return { enteredAtMs, draggingAtEnd };
		});
		const after = await titles(page);
		return { ...r, titlesBefore: before, titlesAfter: after, reorderedDuringB: JSON.stringify(before) !== JSON.stringify(after) };
	},

	async c(page) {
		const rowHeight = await rowHeightOf(page);
		const before = await titles(page);
		await page.evaluate(async (rowHeight) => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const row = document.querySelectorAll(".track")[0];
			const rect = row.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y = rect.top + rect.height / 2;
			const mk = (type, dy) =>
				new PointerEvent(type, { pointerId: 1, clientX: x, clientY: y + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });

			row.dispatchEvent(mk("pointerdown"));
			await wait(650); // 지연이 있는 구현도 확실히 진입하도록 넉넉히 대기
			row.dispatchEvent(mk("pointermove", rowHeight * 1.1)); // 한 칸 아래로 확실히 넘어가도록
			await wait(30);
			row.dispatchEvent(mk("pointerup", rowHeight * 1.1));
			await wait(30);
		}, rowHeight);
		const after = await titles(page);
		const reordered = after[0] === before[1] && after[1] === before[0];
		return { rowHeightPx: Math.round(rowHeight), titlesBefore: before, titlesAfter: after, reorderedBySwappingFirstTwo: reordered };
	},

	async d(page) {
		const rowHeight = await rowHeightOf(page);
		const before = await titles(page);
		await page.evaluate(async (rowHeight) => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const row = document.querySelectorAll(".track")[0];
			const rect = row.getBoundingClientRect();
			const x = rect.left + rect.width / 2;
			const y0 = rect.top + rect.height / 2;
			const mk = (type, pointerId, clientY) =>
				new PointerEvent(type, { pointerId, clientX: x, clientY, bubbles: true, cancelable: true, isPrimary: pointerId === 1, pointerType: "touch" });

			// pointerId=1: 첫 항목을 한 칸 아래로 옮기려는 진짜 제스처
			row.dispatchEvent(mk("pointerdown", 1, y0));
			await wait(200); // long-press-triple-conflict.md §5-5와 동일한 200ms
			// pointerId=2: 같은 행에 다른 손가락이 닿음(첫 번째를 해제하지 않은 채) —
			// 일부러 다른 Y에서 눌러서, 공유 변수(startY 등)가 덮어써지면
			// pointerId=1의 최종 계산이 확실히 어긋나도록 만든다
			row.dispatchEvent(mk("pointerdown", 2, y0 + 500));
			await wait(650);

			row.dispatchEvent(mk("pointermove", 1, y0 + rowHeight * 1.1));
			await wait(30);
			row.dispatchEvent(mk("pointerup", 1, y0 + rowHeight * 1.1));
			await wait(30);
			row.dispatchEvent(mk("pointerup", 2, y0));
			await wait(30);
		}, rowHeight);
		const after = await titles(page);
		const reorderedAsIntended = after[0] === before[1] && after[1] === before[0];
		return { rowHeightPx: Math.round(rowHeight), titlesBefore: before, titlesAfter: after, reorderedAsIntended };
	},
};

const condition = process.argv[2];
const stubPointerCapture = process.argv[3] === "--stub-capture";
if (!condition) {
	console.error("usage: node 01-reorder-no-handle.js <subjects|baseline|treatment> [--stub-capture]");
	process.exit(1);
}
runScenarioFresh(condition, "01-reorder-no-handle", subtests, { stubPointerCapture }).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
