// 채점 기준: nested-interactions/long-press-triple-conflict.md §5 그대로.
//   - 규칙 1: pointerdown 없이 pointermove만 와도 반응하면 안 됨
//   - 규칙 2(같은 행): 두 번째 포인터가 같은 행에 끼어들어도 첫 번째
//     제스처가 오염되면 안 됨(§5-5가 레시피 1에서 발견한 결함의 재현 시도)
//   - 추가 관찰: 서로 다른 행에 동시에 포인터가 있을 때 각 행이
//     독립적으로 동작하는가(원본 문서엔 없지만, 두 조건의 구현 방식
//     차이 — 전역 잠금 vs 행별 격리 — 가 여기서 갈릴 수 있어 관찰한다)
//   - 회귀: 500ms에 메뉴가 실제로 뜨는가

const { runScenarioFresh } = require("./_lib");

const subtests = {
	async rule1_bareMove(page) {
		const before = await page.evaluate(() => document.querySelector(".contact").style.opacity);
		await page.evaluate(() => {
			const row = document.querySelector(".contact");
			const rect = row.getBoundingClientRect();
			row.dispatchEvent(new PointerEvent("pointermove", { pointerId: 1, clientX: rect.left + rect.width, clientY: rect.top + rect.height, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" }));
		});
		const after = await page.evaluate(() => document.querySelector(".contact").style.opacity);
		return { opacityBefore: before, opacityAfterBareMove: after, reactedWithoutPointerdown: before !== after };
	},

	async menuOpensAt500ms(page) {
		const opened = await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const row = document.querySelector(".contact");
			const rect = row.getBoundingClientRect();
			const opts = { pointerId: 1, clientX: rect.left + 10, clientY: rect.top + 10, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" };
			row.dispatchEvent(new PointerEvent("pointerdown", opts));
			await wait(560);
			const menuVisible = document.getElementById("context-menu").style.display === "block";
			row.dispatchEvent(new PointerEvent("pointerup", opts));
			return menuVisible;
		});
		return { menuOpened: opened };
	},

	// 규칙 2(같은 행): pointerId=1이 재정렬 제스처 도중, pointerId=2가
	// 같은 행의 다른 지점을 누름(첫 번째 해제 안 함) → pointerId=1의
	// 원래 제스처(8px 이상 이동 → 재정렬 표시)가 그대로 성립해야 한다.
	async rule2_samRow(page) {
		const r = await page.evaluate(async () => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const row = document.querySelector(".contact");
			const rect = row.getBoundingClientRect();
			const x = rect.left + 10;
			const y0 = rect.top + 10;
			const mk = (type, pointerId, dy) => new PointerEvent(type, { pointerId, clientX: x, clientY: y0 + (dy || 0), bubbles: true, cancelable: true, isPrimary: pointerId === 1, pointerType: "touch" });

			row.dispatchEvent(mk("pointerdown", 1, 0));
			await wait(100);
			row.dispatchEvent(mk("pointerdown", 2, 300)); // 같은 행, 다른 지점에 두 번째 포인터
			await wait(50);
			row.dispatchEvent(mk("pointermove", 1, 20)); // pointerId=1이 20px 이동(>8px) → 재정렬 표시돼야 함
			await wait(20);
			const opacityDuringMove = row.style.opacity;
			row.dispatchEvent(mk("pointerup", 1, 20));
			await wait(20);
			row.dispatchEvent(mk("pointerup", 2, 300));
			await wait(20);
			return { opacityDuringMove };
		});
		return { ...r, reorderIndicatorShown: r.opacityDuringMove === "0.6" };
	},

	// common-pitfalls.md §9 원칙("결과가 예상과 다르면 그레이더부터
	// 의심하라")의 반대 적용: 이번엔 그레이더가 애초에 CONFLICTS.md#C6가
	// 요구하는 결함(네이티브 UI 누출)을 잡을 능력이 있었는지 재확인한다.
	// 기존 a~d(규칙1, 500ms 메뉴, 규칙2, 다른 행 독립)에는 이 항목이
	// 없었다 — 여기 새로 추가한다.
	async androidContextMenuSuppressed(page) {
		const prevented = await page.evaluate(() => {
			const row = document.querySelector(".contact");
			const ev = new MouseEvent("contextmenu", { bubbles: true, cancelable: true });
			row.dispatchEvent(ev);
			return ev.defaultPrevented;
		});
		return { defaultPrevented: prevented, suppressed: prevented === true };
	},

	// iOS 콜아웃 억제(-webkit-touch-callout)는 Playwright/Chromium으로
	// 런타임 검증이 원천적으로 불가능하다(ux-standards-architecture.md
	// §6 — Playwright는 브라우저 엔진만 자동화하고, 이건 WebKit 전용
	// 네이티브 UI라 Chromium엔 대응 동작 자체가 없다). 그래서 이 항목은
	// "선언이 있는가"만 정적으로 확인한다 — 자체 점검이지 [검증됨]이 아니다.
	async iosCalloutSuppressionDeclared(page) {
		const result = await page.evaluate(() => {
			const row = document.querySelector(".contact");
			const cs = getComputedStyle(row);
			// cssRules를 통해 재직렬화된 cssText는 브라우저가 인식 못 하는
			// 벤더 프리픽스(-webkit-touch-callout 등)를 누락시킬 수 있어서,
			// <style> 태그의 원본 textContent를 직접 읽는다 — 파싱/정규화를
			// 거치지 않은 실제 소스 그대로.
			const styleText = [...document.querySelectorAll("style")]
				.map((el) => el.textContent)
				.join("\n");
			return {
				userSelect: cs.userSelect,
				webkitUserSelectDeclaredInSource: /-webkit-user-select\s*:\s*none/.test(styleText),
				webkitTouchCalloutDeclaredInSource: /-webkit-touch-callout\s*:\s*none/.test(styleText),
			};
		});
		return { ...result, note: "선언 존재 여부만 확인 — 실제 iOS 콜아웃 억제 효과는 이 도구로 검증 불가" };
	},

	// 관찰(원본 문서 범위 밖): 서로 다른 행이 동시에 눌려도 각자 독립적으로
	// 동작하는가 — 구현 방식(전역 잠금 vs 행별 격리)에 따라 갈릴 수 있다
	async differentRowsIndependent(page) {
		const r = await page.evaluate(async () => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const rows = document.querySelectorAll(".contact");
			const rowA = rows[0];
			const rowB = rows[1];
			const rectA = rowA.getBoundingClientRect();
			const rectB = rowB.getBoundingClientRect();
			const mkA = (type, dy) => new PointerEvent(type, { pointerId: 1, clientX: rectA.left + 10, clientY: rectA.top + 10 + (dy || 0), bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			const mkB = (type, dy) => new PointerEvent(type, { pointerId: 2, clientX: rectB.left + 10, clientY: rectB.top + 10 + (dy || 0), bubbles: true, cancelable: true, isPrimary: false, pointerType: "touch" });

			rowA.dispatchEvent(mkA("pointerdown", 0));
			await wait(50);
			rowB.dispatchEvent(mkB("pointerdown", 0)); // 다른 행에 별도 손가락
			await wait(50);
			rowB.dispatchEvent(mkB("pointermove", 20)); // rowB를 독립적으로 20px 이동
			await wait(20);
			const rowBOpacityDuringMove = rowB.style.opacity;
			rowB.dispatchEvent(mkB("pointerup", 20));
			rowA.dispatchEvent(mkA("pointerup", 0));
			await wait(20);
			return { rowBOpacityDuringMove };
		});
		return { ...r, rowBWorkedIndependently: r.rowBOpacityDuringMove === "0.6" };
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 09-longpress-triple-favorites.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "09-longpress-triple-favorites", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
