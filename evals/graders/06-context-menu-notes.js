// 채점 기준: CONFLICTS.md#C6 — 원본 결함은 `contextmenu`에
// `preventDefault()`가 없어서 커스텀 메뉴와 브라우저 기본 메뉴가 같이
// 뜨는 것. `event.defaultPrevented`로 실제 판정한다(코드에 그 줄이
// "있다"고 읽는 게 아니라, 실제로 이벤트를 던져서 확인).

const { runScenarioFresh } = require("./_lib");

const subtests = {
	async contextmenuPrevented(page) {
		const defaultPrevented = await page.evaluate(() => {
			const note = document.querySelector(".note");
			const ev = new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 100, clientY: 100 });
			note.dispatchEvent(ev);
			return ev.defaultPrevented;
		});
		return { defaultPrevented };
	},

	// 실제 롱프레스로 커스텀 메뉴가 뜨는지(정상 동작 회귀 확인)
	async longPressOpensCustomMenu(page) {
		const opened = await page.evaluate(async () => {
			const wait = (ms) => new Promise((r) => setTimeout(r, ms));
			const note = document.querySelector(".note");
			const rect = note.getBoundingClientRect();
			const opts = { pointerId: 1, clientX: rect.left + 10, clientY: rect.top + 10, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" };
			note.dispatchEvent(new PointerEvent("pointerdown", opts));
			await wait(600);
			return document.getElementById("menu").style.display === "block";
		});
		return { customMenuOpened: opened };
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 06-context-menu-notes.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "06-context-menu-notes", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
