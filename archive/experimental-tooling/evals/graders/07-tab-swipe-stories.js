// 채점 기준: research/ux-standards/patterns/tab-swipe.md — 원본 결함은
// 탭 전환 스와이프 리스너가 내부 가로 스크롤(#stories)을 제외하지 않아
// 스토리를 넘기면 탭이 바뀌는 것. + common-pitfalls 규칙 1(빈 pointerup).

const { runScenarioFresh } = require("./_lib");

async function currentTabByActiveNav(page) {
	return page.evaluate(() => Number(document.querySelector("nav button.active").dataset.tab));
}

const subtests = {
	// 스토리 영역에서 좌우로 크게 드래그해도 탭이 바뀌면 안 됨
	async swipeOnStoriesMustNotChangeTab(page) {
		const before = await currentTabByActiveNav(page);
		await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const story = document.querySelector(".story");
			const rect = story.getBoundingClientRect();
			const y = rect.top + rect.height / 2;
			const opts = (x) => ({ pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			story.dispatchEvent(new PointerEvent("pointerdown", opts(rect.left + 30)));
			await wait(20);
			story.dispatchEvent(new PointerEvent("pointerup", opts(rect.left - 100))); // 130px 왼쪽으로, 임계값(60px) 훌쩍 넘김
			await wait(20);
		});
		const after = await currentTabByActiveNav(page);
		return { tabBefore: before, tabAfter: after, tabStayedSame: before === after };
	},

	// 일반 콘텐츠 영역(피드 카드 위)에서 스와이프하면 탭이 정상적으로 바뀌어야 함
	async swipeOnFeedStillChangesTab(page) {
		const before = await currentTabByActiveNav(page);
		await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const feedItem = document.querySelector(".feed-item");
			const rect = feedItem.getBoundingClientRect();
			const y = rect.top + rect.height / 2;
			const opts = (x) => ({ pointerId: 1, clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" });
			feedItem.dispatchEvent(new PointerEvent("pointerdown", opts(rect.left + rect.width - 20)));
			await wait(20);
			feedItem.dispatchEvent(new PointerEvent("pointerup", opts(rect.left - 100)));
			await wait(20);
		});
		const after = await currentTabByActiveNav(page);
		return { tabBefore: before, tabAfter: after, tabAdvanced: after === before + 1 };
	},

	// 규칙 1: pointerdown 없이 콘텐츠 영역에 pointerup만 오면 탭이 바뀌면 안 됨
	async rule1_bareUp(page) {
		const before = await currentTabByActiveNav(page);
		await page.evaluate(() => {
			const content = document.getElementById("content");
			const rect = content.getBoundingClientRect();
			content.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1, clientX: rect.left + 10, clientY: rect.top + 200, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" }));
		});
		const after = await currentTabByActiveNav(page);
		return { tabBefore: before, tabAfter: after, reactedWithoutPointerdown: before !== after };
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 07-tab-swipe-stories.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "07-tab-swipe-stories", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
