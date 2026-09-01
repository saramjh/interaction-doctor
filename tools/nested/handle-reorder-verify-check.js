const { chromium } = require("/Users/ojihun/DEV/interaction-doctor/evals/node_modules/playwright");

const URL = "file:///Users/ojihun/DEV/interaction-doctor/demo/demo-reorder.html";

async function main() {
	const browser = await chromium.launch();
	const page = await browser.newPage({ viewport: { width: 390, height: 700 } });
	await page.goto(URL);
	await page.click("#btnAfter");
	await page.waitForTimeout(30);

	const results = {};

	// a) 핸들 클릭 즉시(0ms) 드래그 시작
	results.a_handleImmediate = await page.evaluate(() => {
		const handle = document.querySelectorAll(".handle")[0];
		const li = handle.closest(".track");
		const before = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		handle.dispatchEvent(new PointerEvent("pointerdown", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 100 }));
		const liftedImmediatelyAfterDown = li.classList.contains("lifted");
		// 지연 없이 바로 다음 move
		document.dispatchEvent(new PointerEvent("pointermove", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 130 }));
		const after = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		document.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 130 }));
		return { before, liftedImmediatelyAfterDown, after, changed: before.transform !== after.transform };
	});

	// b) 카드 본문 클릭 → 무반응
	results.b_cardBodyNoReaction = await page.evaluate(() => {
		const li = document.querySelectorAll(".track")[1];
		const meta = li.querySelector(".meta");
		const before = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		meta.dispatchEvent(new PointerEvent("pointerdown", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 200 }));
		document.dispatchEvent(new PointerEvent("pointermove", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 260 }));
		const after = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		document.dispatchEvent(new PointerEvent("pointerup", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 260 }));
		return { before, after, unchanged: before.transform === after.transform && before.lifted === after.lifted };
	});

	// c) 규칙 1 — pointerdown 없이 핸들에 bare pointermove만 오면 무반응
	results.c_rule1_bareMoveNoReaction = await page.evaluate(() => {
		const handle = document.querySelectorAll(".handle")[2];
		const li = handle.closest(".track");
		const before = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		document.dispatchEvent(new PointerEvent("pointermove", { pointerId: 99, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 100, clientY: 400 }));
		const after = { transform: li.style.transform, lifted: li.classList.contains("lifted") };
		return { before, after, unaffected: before.transform === after.transform && before.lifted === after.lifted };
	});

	// d) 규칙 2 — 핸들1(포인터1) 드래그 도중 핸들2(포인터2)가 끼어들어도
	// 포인터1은 정상 동작, 포인터2는 완전히 무시되는지
	results.d_rule2_multiPointer = await page.evaluate(async () => {
		const wait = (ms) => new Promise((r) => setTimeout(r, ms));
		const handles = document.querySelectorAll(".handle");
		const handleA = handles[0];
		const handleB = handles[1];
		const liA = handleA.closest(".track");
		const liB = handleB.closest(".track");

		handleA.dispatchEvent(new PointerEvent("pointerdown", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 50, clientY: 100 }));
		await wait(20);
		// 포인터1이 아직 활성인 상태에서 포인터2가 다른 핸들을 누름(해제 안 함)
		handleB.dispatchEvent(new PointerEvent("pointerdown", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: false, pointerType: "touch", clientX: 50, clientY: 300 }));
		await wait(20);
		const liBLiftedAfterInterference = liB.classList.contains("lifted");

		// 포인터1을 계속 이동 — 정상 동작해야 함
		document.dispatchEvent(new PointerEvent("pointermove", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 50, clientY: 400 }));
		await wait(20);
		const liATransformAfterMove = liA.style.transform;

		// 포인터2도 이동시켜봄 — 완전히 무시돼야 함(liB 안 움직임)
		document.dispatchEvent(new PointerEvent("pointermove", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: false, pointerType: "touch", clientX: 50, clientY: 600 }));
		await wait(20);
		const liBTransformAfterPointer2Move = liB.style.transform;

		// 포인터2 해제 — 아무 효과 없어야 함(liA 여전히 lifted 유지)
		document.dispatchEvent(new PointerEvent("pointerup", { pointerId: 2, bubbles: true, cancelable: true, isPrimary: false, pointerType: "touch", clientX: 50, clientY: 600 }));
		await wait(20);
		const liAStillLiftedAfterPointer2Up = liA.classList.contains("lifted");

		// 포인터1 정상 해제
		document.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1, bubbles: true, cancelable: true, isPrimary: true, pointerType: "touch", clientX: 50, clientY: 400 }));
		await wait(20);

		return {
			liBLiftedAfterInterference,      // false여야 함(포인터2 무시)
			liATransformChanged: liATransformAfterMove !== "none" && liATransformAfterMove !== "",
			liBTransformAfterPointer2Move,   // ""(빈 문자열)이어야 함(포인터2 완전 무시)
			liAStillLiftedAfterPointer2Up,   // true여야 함(포인터2의 up이 포인터1 제스처를 안 끊음)
		};
	});

	console.log(JSON.stringify(results, null, 2));
	await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
