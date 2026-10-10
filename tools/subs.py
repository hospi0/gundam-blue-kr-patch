# -*- coding: utf-8 -*-
r"""건담 외전 I 음성 자막 자료(2026-10-10 PoC) — 번역 줄 → 쪽 → 덩어리별 묶음(다이노 poc2.payload 꼴) → 상주 블롭 표.
  묶음:  +0 'DSUB' · +4 u16 쪽 수 · +6 u16 0 · +12 u16 글꼴 자리 · +16 쪽 표[쪽 수](u16 t0, u16 t1, u16 쪽 자리, u16 0)
         쪽 = glyphpack 꼴(u8 w8, u8 nrow, u8 c0, u8 글자 수, 글자마다 3 B) · 글꼴 = 글자마다 18 B(12×12 1비트)
         t = 1/60초, 덩어리 처음부터(머리 없음).
  블롭 표: 스트림 번호(SS_SND 표 번호 − 6 = 0x06014224 값) 0‥31 → 묶음 주소(없으면 0).
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.append(r'C:\claude\project\burningrangers-kr-patch\tools')
import glyphpack as G

G.MAXW = 300
MINP = 0.8; LINGER = 0.3
PUNCT_SP = re.compile(r'([,.!?:;)\]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥]) +')

# ★PoC 번역(2026-10-10, 받아쓰기 오류 바로잡음: 優勝位→ユウ少尉 · 誤兆→伍長 · 統治下→トーチカ · ご分→ご武運 · ミディア→ミデア)
POC = {
    'V25': [
        (11.22, 12.44, '유우 소위님.'),
        (13.16, 18.30, '오늘부터 이 부대의 통신 오퍼레이터가 된'),
        (18.30, 21.44, '모린 키타무라 오장입니다.'),
        (23.04, 25.80, '이미 아시겠지만'),
        (25.80, 32.26, '다시 한번 이번 작전에 대해 설명드리겠습니다.'),
        (35.16, 39.40, '여러분은 이대로 미데아로 이동해'),
        (39.40, 42.70, '포인트 36에서 강하,'),
        (43.36, 48.70, '거기서 4시 방향으로 1킬로미터 간 곳에 있는'),
        (48.70, 52.04, '지온 기지를 공격해 주십시오.'),
        (53.90, 62.76, '적 기지는 방어용 토치카로 지켜지고 있으니 충분히 주의해 주십시오.'),
        (65.22, 73.82, '또한 이번 작전의 목적은 모빌슈트끼리의 전투 데이터 수집입니다.'),
        (74.66, 85.30, '기지를 파괴하기 전이라도 적 모빌슈트를 전부 섬멸하면 즉시 철수해 주십시오.'),
        (88.22, 91.78, '그럼 무운을 빌겠습니다.'),
    ],
    'V07': [
        (0.00, 2.54, '미노프스키 입자 농도 62.'),
        (3.98, 8.04, '이 정도면 적에게 들키지 않고 접근할 수 있겠습니다.'),
        (9.02, 13.00, '그럼 슬슬 가 볼까.'),
        (15.42, 17.46, '먼저 간다!'),
        (18.16, 19.34, '유우 소위!'),
    ],
}


def clean(t):
    return PUNCT_SP.sub(r'\1', t.strip())


def check_glyphs(t, where):
    for c in t:
        if c == ' ': continue
        if not any(G.glyph(c)): raise SystemExit('글꼴에 없는 글자 %r — %s' % (c, where))


def pages_for(rows):
    """[(초, 초, 번역)] → [(t0초, t1초, [줄…])] — 다이노 build.pages_for 와 같음"""
    rows = sorted(rows); out = []
    for i, (s, e, ko) in enumerate(rows):
        ko = clean(ko); check_glyphs(ko, ko)
        nxt = rows[i + 1][0] if i + 1 < len(rows) else None
        pg = G.pages_of(ko)
        lens = [max(1, len(''.join(p).replace(' ', ''))) for p in pg]; tot = sum(lens); acc = 0
        end = max(e + LINGER, s + MINP * len(pg))
        if nxt is not None: end = min(end, max(nxt, s + MINP * len(pg)))
        for p, L in zip(pg, lens):
            t0 = s + (end - s) * acc / tot; acc += L
            out.append([t0, s + (end - s) * acc / tot, p])
    for a, b in zip(out, out[1:]):
        if a[1] > b[0]: a[1] = b[0]
    return [(a, b, p) for a, b, p in out]


def payload(rows):
    pages = [(int(round(a * 60)), int(round(b * 60)), p) for a, b, p in pages_for(rows)]
    lay = [G.layout(l) for _, _, l in pages]
    gl = []; gi = {}
    for _, _, chars in lay:
        for c, _, _ in chars:
            if c not in gi: gi[c] = len(gl); gl.append(c)
    if len(gl) > 511: raise SystemExit('서로 다른 글자 %d > 511' % len(gl))
    recs = []
    for w8, nrow, chars in lay:
        assert w8 * nrow <= 255 and w8 <= 40
        r = bytes([w8, nrow, (40 - w8) // 2, len(chars)])
        for c, x, ln in chars:
            r += bytes([gi[c] & 0xFF, x & 0xFF, (x >> 8) | ln << 1 | (gi[c] >> 8) << 2])
        recs.append(r + bytes(-len(r) % 4))
    offs = []; o = 16 + 8 * len(pages)
    for r in recs: offs.append(o); o += len(r)
    tab = b''.join(struct.pack('>HHHH', t0, t1, offs[i], 0) for i, (t0, t1, _) in enumerate(pages))
    b = b'DSUB' + struct.pack('>HH', len(pages), 0) + bytes(4) + struct.pack('>H', o) + bytes(2) + tab + b''.join(recs) + b''.join(G.gbytes(c) for c in gl)
    return b + bytes(-len(b) % 4), pages


TSV = os.path.join(ROOT, 'work', 'text', 'voice_ko.tsv')


def load():
    """work/text/voice_ko.tsv(id·시작·끝·원문·번역) → {'V25': [(초, 초, 번역)…]} — 번역 빈 줄은 자막 없음"""
    out = {}
    for ln in open(TSV, encoding='utf-8').read().splitlines()[1:]:
        c = ln.split('	')
        if len(c) < 5 or not c[4].strip(): continue
        out.setdefault(c[0].split('_')[0], []).append((float(c[1]), float(c[2]), c[4].strip()))
    return out


def blob(base, voices=None):
    voices = voices or load()
    """상주 자료: 표 32×u32(스트림 번호 → 묶음 주소) + 묶음들"""
    tab = [0] * 32; body = bytearray(); info = {}
    for v, rows in sorted(voices.items()):
        k = int(v[1:]) - 6
        b, pages = payload(rows)
        tab[k] = base + 128 + len(body); body += b; info[v] = (len(pages), len(b))
    return struct.pack('>32I', *tab) + bytes(body), info
