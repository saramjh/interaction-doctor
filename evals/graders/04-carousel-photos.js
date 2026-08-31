// 채점 기준: research/ux-standards/patterns/carousel.md — "한 번에 하나씩
// 온전히 감상"류 콘텐츠는 scroll-snap-type: x mandatory + scroll-snap-align
// (+ scroll-snap-stop: always로 플링 시 여러 장 건너뛰지 못하게)를 권장한다.
// 원본 결함은 scroll-snap 자체가 없어서 스와이프 후 임의 위치에 멈추는 것.
//
// 실제로 스크롤을 프로그래매틱하게 흔들어 놓고 브라우저 자체 스냅
// 메커니즘이 정렬해주는지 관찰한다(정적으로 CSS 값만 읽지 않는다).
// scroll-snap-stop의 "플링으로 여러 장 건너뛰지 못한다" 효과는 실제
// 관성 스크롤이 필요해서 이 도구(합성 이벤트)로는 확인할 수 없다 —
// 이 프로젝트가 이미 여러 번 확인한 한계이므로 구조적 존재 여부만
// 관찰하고 pass/fail을 매기지 않는다.

const { runScenarioFresh } = require("./_lib");

const subtests = {
	async structuralSnap(page) {
		return page.evaluate(() => {
			const viewer = document.getElementById("viewer");
			const photo = document.querySelector(".photo");
			const vs = getComputedStyle(viewer);
			const ps = getComputedStyle(photo);
			return {
				scrollSnapType: vs.scrollSnapType,
				photoScrollSnapAlign: ps.scrollSnapAlign,
				photoScrollSnapStop: ps.scrollSnapStop, // 참고용 관찰, pass/fail 아님
			};
		});
	},

	// 사진 사이 임의 위치(1.4번째 사진 지점)로 "부드러운" 스크롤(휠 스와이프
	// 흉내)을 걸고, scrollend까지 실제로 기다린 뒤 브라우저 자체 snap
	// 엔진이 정확히 사진 경계로 정렬해주는지 확인한다.
	async misalignedThenSettles(page) {
		const photoWidth = await page.evaluate(() => document.querySelector(".photo").getBoundingClientRect().width);
		const scrollLeftFinal = await page.evaluate((target) => {
			return new Promise((resolve) => {
				const viewer = document.getElementById("viewer");
				viewer.addEventListener("scrollend", () => resolve(viewer.scrollLeft), { once: true });
				viewer.scrollTo({ left: target, behavior: "smooth" });
				// scrollend가 어떤 이유로든 안 오면 안전망으로 1.5s 후 현재값 반환
				setTimeout(() => resolve(viewer.scrollLeft), 1500);
			});
		}, Math.round(photoWidth * 1.4));

		const remainder = scrollLeftFinal % photoWidth;
		const distanceToNearestBoundary = Math.min(remainder, photoWidth - remainder);
		return {
			photoWidthPx: Math.round(photoWidth),
			targetedScrollLeft: Math.round(photoWidth * 1.4),
			scrollLeftFinal: Math.round(scrollLeftFinal),
			distanceToNearestBoundaryPx: Math.round(distanceToNearestBoundary),
			snappedToPhotoBoundary: distanceToNearestBoundary < 2,
		};
	},
};

const condition = process.argv[2];
if (!condition) {
	console.error("usage: node 04-carousel-photos.js <subjects|baseline|treatment>");
	process.exit(1);
}
runScenarioFresh(condition, "04-carousel-photos", subtests).catch((e) => {
	console.error("GRADER CRASHED:", e);
	process.exit(1);
});
