// 채점 기준: nested-interactions/side-drawer-back-gesture.md(레시피 3) —
// 이건 "해소 규칙"이 아니라 "완화 조치" 목록이라는 게 원본 문서 자체의
// 결론이다. 그래서 여기서도 "충돌이 해소됐는가"가 아니라 레시피 3이
// 제시한 완화 조치가 실제로 구현됐는지만 확인한다:
//   - 완화 2: 엣지 스와이프가 왼쪽(iOS 시스템 뒤로가기 영역)이 아닌
//     다른 위치에 있는가(관찰만, 필수 아님)
//   - 완화 3: 스와이프가 시스템에 뺏겨도 항상 열 수 있는 버튼 경로가
//     있는가 — 이게 원래 request.txt가 요구한 핵심이라 이것만 pass/fail로 매긴다
// 완화 1(overscroll-behavior-x)의 실제 효과는 이 도구로 검증 불가하다는
// 게 이미 이 프로젝트에서 실험으로 확인돼 있다 — 존재 여부만 관찰한다.

const { runScenarioFresh } = require("./_lib");

const subtests = {
	async alwaysAvailableButtonExists(page) {
		// 엣지 스와이프 존(#edge-zone) 밖에 있는, 드로어를 여는 버튼을 찾는다
		return page.evaluate(() => {
			const buttons = Array.from(document.querySelectorAll("button"));
			const candidates = buttons.filter((b) => {
				const insideEdgeZone = b.closest("#edge-zone");
				const text = (b.textContent || "") + (b.getAttribute("aria-label") || "");
				return !insideEdgeZone && /메뉴|menu|☰/i.test(text);
			});
			return { found: candidates.length > 0, count: candidates.length, ids: candidates.map((b) => b.id || b.textContent.trim()) };
		});
	},

	async clickingButtonActuallyOpensDrawer(page) {
		const found = await page.evaluate(() => {
			const buttons = Array.from(document.querySelectorAll("button"));
			const btn = buttons.find((b) => !b.closest("#edge-zone") && /메뉴|menu|☰/i.test((b.textContent || "") + (b.getAttribute("aria-label") || "")));
			return !!btn;
		});
		if (!found) return { skipped: "no always-available button found" };

		const beforeOpen = await page.evaluate(() => document.getElementById("drawer").classList.contains("open"));
		await page.evaluate(() => {
			const buttons = Array.from(document.querySelectorAll("button"));
			const btn = buttons.find((b) => !b.closest("#edge-zone") && /메뉴|menu|☰/i.test((b.textContent || "") + (b.getAttribute("aria-label") || "")));
			btn.click();
		});
		const afterOpen = await page.evaluate(() => document.getElementById("drawer").classList.contains("open"));
		return { beforeOpen, afterOpen, buttonActuallyOpensDrawer: !beforeOpen && afterOpen };
	},

	// 참고용 관찰(완화 2, pass/fail 아님): 엣지 스와이프 존이 화면 왼쪽인지 오른쪽인지
	async observeEdgeZoneSide(page) {
		return page.evaluate(() => {
			const zone = document.getElementById("edge-zone");
			if (!zone) return { exists: false };
			const cs = getComputedStyle(zone);
			const rect = zone.getBoundingClientRect();
			return { exists: true, cssLeft: cs.left, cssRight: cs.right, boundingLeftX: Math.round(rect.left), viewportWidth: window.innerWidth, onLeftEdge: rect.left < 5 };
		});
	},

	// 참고용 관찰(완화 1, pass/fail 아님 — 실제 효과 검증 불가는 이미 알려진 한계)
	async observeOverscrollBehavior(page) {
		return page.evaluate(() => ({ htmlOverscrollBehaviorX: getComputedStyle(document.documentElement).overscrollBehaviorX }));
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 08-side-drawer-menu.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "08-side-drawer-menu", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
