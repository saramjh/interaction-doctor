// 채점 기준: 이 시나리오의 원본 결함(다중 선택 모드 진입 후 클로저에
// 캡처된 첫 타일만 토글되는 것)이 실제로 고쳐졌는지 + common-pitfalls
// 규칙 2에 해당하는 변형(두 타일에 걸친 공유 상태 오염) 관찰.
// research/ux-standards/patterns/multi-select.md는 실행 코드(§5)가 없는
// 조사 문서라 별도 수치 기준은 없다 — 원본 결함 재현 여부가 핵심 기준이다.

const { runScenarioFresh } = require("./_lib");

async function longPress(page, tileIndex) {
	// 실제 터치는 롱프레스로 끝나도(눌렀다 뗀 지점이 안 움직였으면) 그
	// 위에서 곧이어 click을 한 번 더 합성해준다 — tap()과 동일하게
	// pointerdown → pointerup → click 순서를 지킨다. 이전에 click을
	// 안 던졌더니 "다음 탭이 막힌다"는 게 진짜 결함인지 테스트 쪽
	// 결함인지 구분이 안 됐다(05번 채점 초기에 한 번 겪었던 것과
	// 같은 종류의 함정).
	await page.evaluate(async (idx) => {
		const wait = (ms) => new Promise((r) => setTimeout(r, ms));
		const tile = document.querySelectorAll(".photo")[idx];
		const opts = { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" };
		tile.dispatchEvent(new PointerEvent("pointerdown", opts));
		await wait(600);
		tile.dispatchEvent(new PointerEvent("pointerup", opts));
		tile.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await wait(20);
	}, tileIndex);
}

// 실제 터치 탭은 브라우저가 pointerdown → pointerup → click 순으로
// 합성해준다 — click 하나만 던지면 실제 터치와 다른 경로를 타서
// preventClick류 상태 초기화 타이밍이 왜곡된다. 세 이벤트를 다 던져서
// 실제 탭에 최대한 가깝게 만든다.
async function tap(page, tileIndex, pointerId = 99) {
	await page.evaluate(({ idx, pointerId }) => {
		const tile = document.querySelectorAll(".photo")[idx];
		const opts = { pointerId, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch" };
		tile.dispatchEvent(new PointerEvent("pointerdown", opts));
		tile.dispatchEvent(new PointerEvent("pointerup", opts));
		tile.dispatchEvent(new MouseEvent("click", { bubbles: true }));
	}, { idx: tileIndex, pointerId });
}

async function selectedIndices(page) {
	return page.evaluate(() => Array.from(document.querySelectorAll(".photo.selected")).map((el) => Number(el.dataset.index)));
}

const subtests = {
	// 원본 결함의 핵심: 0번을 롱프레스로 선택 모드 진입 후 3번을 탭하면
	// 3번이 선택돼야 한다(원본 결함은 계속 0번만 토글됨)
	async tapOtherTileAfterEnteringSelectMode(page) {
		await longPress(page, 0);
		const afterLongPress = await selectedIndices(page);
		await tap(page, 3);
		const afterTapOther = await selectedIndices(page);
		return {
			afterLongPress,
			afterTapOther,
			tile3GotSelected: afterTapOther.includes(3),
			tile0StayedSelected: afterTapOther.includes(0),
			bugPresent_onlyFirstTileToggles: !afterTapOther.includes(3) && afterLongPress.includes(0),
		};
	},

	// 여러 타일을 연속으로 탭해서 전부 각자 독립적으로 선택되는지
	async multipleTilesIndependentlyToggle(page) {
		await longPress(page, 0);
		await tap(page, 2);
		await tap(page, 5);
		await tap(page, 7);
		const result = await selectedIndices(page);
		result.sort((a, b) => a - b);
		return { selected: result, expected: [0, 2, 5, 7], allFourIndependentlySelected: JSON.stringify(result) === JSON.stringify([0, 2, 5, 7]) };
	},

	// 규칙 2류: 0번 롱프레스 타이머가 도는 도중(500ms 되기 전) 1번을
	// 눌렀다 뗀다 — 공유 변수(preventClick 등)가 오염되어 이후 0번의
	// 정상 진입/토글 흐름이 깨지는지 관찰
	async concurrentPressOnDifferentTile(page) {
		const r = await page.evaluate(async () => {
			const wait = (ms) => new Promise((res) => setTimeout(res, ms));
			const tiles = document.querySelectorAll(".photo");
			const t0 = tiles[0];
			const t1 = tiles[1];
			const mk = (el, type, pointerId) => el.dispatchEvent(new PointerEvent(type, { pointerId, bubbles: true, cancelable: true, isPrimary: pointerId === 1, pointerType: "touch" }));

			mk(t0, "pointerdown", 1); // 0번 롱프레스 타이머 시작(500ms 뒤 진입 예정)
			await wait(150);
			mk(t1, "pointerdown", 2); // 그 사이에 1번을 짧게 누름
			await wait(50);
			mk(t1, "pointerup", 2); // 1번은 롱프레스 안 채우고 뗌(짧은 탭)
			await wait(450); // 0번의 500ms가 마저 지나도록 대기
			return {};
		});
		const selected = await selectedIndices(page);
		return { selectedAfter: selected, tile0Entered: selected.includes(0), tile1NotAffected: !selected.includes(1) };
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 05-multi-select-photos.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "05-multi-select-photos", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
