# 기동전사 건담 외전 I 전율의 블루 한글 패치 (Mobile Suit Gundam Side Story I - Senritsu no Blue, 세가 새턴 일본판)

- 대상: Mobile Suit Gundam Side Story I - Senritsu no Blue (Japan) — 트랙 01에 xdelta 패치 (트랙 02~12 오디오·cue 는 그대로, 트랙 01 크기도 그대로)
- 내려받기: 릴리즈의 `GundamSideStory1_KR_v0.9.zip` — 안의 readme.txt 에 원본·패치 md5 와 적용 방법

| 트랙 | 원본 md5 | 패치 md5 |
|---|---|---|
| Track 01 | `E32048A2AEFF073DB25A93C80E2791A5` | `E39E4817ED629779364670D03D996847` |

## 바뀌는 것 (v0.9)
- 음성 자막 143줄 — 원래 자막이 없는 게임이라 새로 넣음(브리핑·미션 전후 컷신·결과 화면 내레이션, 음성 재생 위치에 맞춰 넘어감)
- 동영상 자막: 오프닝, 다음 편 예고
- 결과 화면: 교관 평가·실패 메시지 14장, 항목 이름(전술득점·피탄율·종합전적·평가), 계급(소위·중위·대위·소령)
- STAGE SELECT 화면: 제N화·시나리오 제목·전술득점·피탄율·종합전적·평가
- 시나리오 제목 5장, 타이틀 로고 부제(전율의 블루)

## 알려진 점
- 인게임 HUD·포즈·STATUS 등 영문 그림은 그대로
- 자막 원문은 음성을 받아쓴 것이라 일부 대사가 실제와 다를 수 있음

## 저장소
- `tools/build.py` 빌더 · `hook.py` 자막 훅(SH-2, SGL 명령표에 VDP1 스프라이트) · `subs.py` 자막 묶음 · `scgfx.py` 그림 · `moviesub.py` 동영상 자막 · `iso.py` 디스크(트랙 크기 그대로) · `make_dist.py` 배포
- `tools/test_hook.py` SH-2 흉내기(`sh2sim.py`) 검산 · `asr_all.py` 받아쓰기(스테레오)
- `work/text/voice_ko.tsv` 음성 자막(id·시각·원문·번역)
- `docs/` 조사·작업 기록
