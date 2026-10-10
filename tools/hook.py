# -*- coding: utf-8 -*-
r"""건담 외전 I 음성 자막 훅(2026-10-10 PoC) — 다이노 hook.py(VDP1 스프라이트판) 를 옮김.
  · 자리: 하위 워크 RAM RES = 0x00244800(S0_1.BIN 을 0x44800 까지 0 으로 채우고 뒤에 붙임 → S0_1 적재 0x00200000 에 같이 실림).
          S0_0 시작 코드가 S0_1 을 먼저 불러온 뒤(0x06020102) 화면 초기화(0x06031B74 → 0x06044B38)에서 VBI 를 등록하므로 등록 때 이미 있음.
  · VBI: S0_0 의 VBlank-OUT 등록 리터럴 0x06044BE8(원래 0x060449D6) → 우리 감싸개(원래 처리기 먼저 부르고 sub). ★IN 이 아니라 OUT — 명령표 DMA(IN) 뒤·다음 프레임 그리기(IN 의 프레임 전환) 전.
  · 시계: 스트림 구조 0x06014220(1.BIN 상주) — +0x0C 상태 3 = 재생 중 · +0x04 스트림 번호 · +0x18 소리 칩에 넘긴 바이트(0x2000 단위).
          t(1/60초) = 넘긴 바이트 ÷ 735 − LEAD + 바뀐 뒤 센 프레임(최대 STEP). 표 RES+TAB[번호] → 묶음(없으면 자막 없음).
  · 그림: 1비트 버퍼에 찍기(버닝 레인저 stamp) → 16비트 RGB 선형 그림(0 투명 · 0x8000 검정 테두리 · 0xFFFF 흰 글자)을 VDP1 VRAM 0x70800
          (0x70400‥0x7FF00 = 스테이트 14장 모두 채움 0x8000 그대로 = 안 씀 · 0x7FF00 은 게임이 씀).
  · 명령: 보통 스프라이트(종류 0) PMOD 0x00A8(RGB·끝 코드 끔) · 좌표는 게임 지역 좌표(160,112) 기준 → XA = −w8·4, YA = 104 − nrow·8.
          매 VBI 뒤 명령표(0x25C00000)를 END 까지 훑어 그 칸만 «건너뛰고 점프(0x5000) → 우리 칸 0x7F000(명령+END)». 꺼지면 END 로.
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sh2asm import A

mov = lambda m, n: 0x6003 | n << 8 | m << 4
ldb = lambda m, n: 0x6000 | n << 8 | m << 4
ldbp = lambda m, n: 0x6004 | n << 8 | m << 4
stb = lambda m, n: 0x2000 | n << 8 | m << 4
ldb0 = lambda m, d: 0x8400 | m << 4 | d
stb0 = lambda n, d: 0x8000 | n << 4 | d
exb = lambda m, n: 0x600C | n << 8 | m << 4
exw = lambda m, n: 0x600D | n << 8 | m << 4
OR = lambda m, n: 0x200B | n << 8 | m << 4
AND = lambda m, n: 0x2009 | n << 8 | m << 4
ADD = lambda m, n: 0x300C | n << 8 | m << 4
addi = lambda n, i: 0x7000 | n << 8 | (i & 0xFF)
movi = lambda n, i: 0xE000 | n << 8 | (i & 0xFF)
shll = lambda n: 0x4000 | n << 8; shlr = lambda n: 0x4001 | n << 8
shll2 = lambda n: 0x4008 | n << 8; shlr2 = lambda n: 0x4009 | n << 8
shll8 = lambda n: 0x4018 | n << 8; shlr8 = lambda n: 0x4019 | n << 8
shll16 = lambda n: 0x4028 | n << 8; shlr16 = lambda n: 0x4029 | n << 8
dt = lambda n: 0x4010 | n << 8
push = lambda m: 0x2F06 | m << 4; pop = lambda n: 0x60F6 | n << 8

RES = 0x00244800                     # 코드
DATA = RES + 0x800                   # 변수·명령
BUF = RES + 0x900; BSTR = 52         # 1비트 쪽 버퍼 52 B × 34행
TAB = RES + 0x1000                   # 스트림 번호 → 묶음 표 + 묶음들(subs.blob)
END = 0x00250000                     # Sn_1/SC_1 적재 시작 — 넘으면 안 됨
VBI = 0x060449D6; VBI_LIT = 0x06044BE8           # ★VBlank-OUT(2026-10-10 PoC 1차 VBlank-IN 은 안 보임: IN 처리기가 명령표를 SCU DMA 로 보내고 PTMR=2 라 프레임 전환 때 바로 그림 → IN 뒤에 넣으면 늦고 다음 DMA 에 지워짐)
STREAM = 0x06014220
TEX = 0x25C70800; TEXA = (TEX & 0x7FFFF) // 8
LIST = 0x25C00000
OWN = 0x25C7F000; OWNL = (OWN & 0x7FFFF) // 8
LEAD = 25; STEP = 12


def data_part():
    data = bytearray(); lab = {}
    def put(name, b):
        nonlocal data
        data += bytes(-len(data) % 4); lab[name] = DATA + len(data); data += b
    put('cur', bytes(4)); put('lcd', bytes(4)); put('cnt', bytes(4)); put('pay', bytes(4))
    put('cmd', struct.pack('>16H', 0x0000, 0, 0x00A8, 0, TEXA, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    assert DATA + len(data) <= BUF
    return bytes(data), lab


def assemble():
    data, dlab = data_part()
    a = A(RES); a.lab.update(dlab); W = a.w
    # ---- VBI 감싸개 ----
    a.L('vbi'); W(0x4F22); a.ld(0, VBI); W(0x400B, 0x0009)
    W(0x4F02, 0x4F12)                                                  # MACH·MACL 보존(시계에 dmulu)
    a.br('bsr', 'sub'); W(0x0009)
    W(0x4F16, 0x4F06, 0x4F26, 0x000B, 0x0009)
    # ---- sub ----
    a.L('sub'); W(0x4F22)
    a.ld(1, STREAM); W(0x5013, 0x8803); a.br('bf', 'none')            # 상태 +0x0C == 3(재생 중)
    W(0x5011, 0x8820); a.br('bt', 'none')                              # (번호 32 이상이면 없음 — cmp/eq 로는 못 거르므로 아래 and)
    W(0xC91F, shll2(0)); a.ld(2, TAB); W(0x042E, 0x2448); a.br('bt', 'none')   # r4 = 표[번호 & 31]
    a.ld(2, 'pay'); W(0x2242)
    W(0x5316, 0x2338); a.br('bt', 'none')                             # r3 = 넘긴 바이트(+0x18)
    a.ld(1, 'lcd'); W(0x6012, 0x3030); a.br('bt', 'samecd')
    W(0x2132); a.ld(1, 'cnt'); W(movi(0, 0), 0x2102); a.br('bra', 'calc'); W(0x0009)
    a.L('samecd'); a.ld(1, 'cnt'); W(0x6012, movi(2, STEP), 0x3022); a.br('bt', 'calc')
    W(addi(0, 1), 0x2102)
    a.L('calc'); a.ld(2, 0x592A25); W(0x3325, 0x030A)               # mach = 바이트 × (2^32/735) 의 위 32비트
    a.ld(1, 'cnt'); W(0x6012, ADD(0, 3), addi(3, -LEAD))
    W(0x8542, exw(0, 6)); W(mov(4, 1), addi(1, 16))                    # r6 = 쪽 수, r1 = 쪽 표
    W(0x2668); a.br('bt', 'none')
    a.L('lp'); W(0x6015, exw(0, 0), 0x3303); a.br('bf', 'nx')
    W(0x6011, exw(0, 0), 0x3037); a.br('bf', 'nx')
    W(0x8511, exw(0, 5), ADD(4, 5)); a.br('bra', 'have'); W(0x0009)
    a.L('nx'); W(addi(1, 6), dt(6)); a.br('bf', 'lp')
    a.L('none'); W(movi(5, 0))
    a.L('have'); a.ld(1, 'cur'); W(0x6012, 0x3050); a.br('bt', 'same')
    W(0x2152, 0x2558); a.br('bt', 'off')
    a.br('bsr', 'draw'); W(mov(5, 1))
    a.L('on')
    a.ld(1, LIST); a.ld(3, 1024)
    a.L('il'); W(0x6011, exw(0, 0)); a.ld(2, 0x8000); W(0x3020); a.br('bt', 'iput')
    a.ld(2, 0x5000); W(0x3020); a.br('bf', 'inx')
    W(0x8511, exw(0, 0)); a.ld(2, OWNL); W(0x3020); a.br('bt', 'iput')
    a.L('inx'); W(addi(1, 32), dt(3)); a.br('bf', 'il')
    a.br('bra', 'ret'); W(0x0009)
    a.L('iput')                                                        # 게임 END 칸만 «건너뛰고 점프 → 우리 칸»
    a.ld(0, 0x5000); W(0x2101); a.ld(0, OWNL); W(0x8111)
    a.ld(1, OWN); a.ld(2, 'cmd'); W(movi(3, 8))
    a.L('ic'); W(0x6026, 0x2102, addi(1, 4), dt(3)); a.br('bf', 'ic')
    a.ld(0, 0x8000); W(0x2101)
    a.br('bra', 'ret'); W(0x0009)
    a.L('same'); W(0x2558); a.br('bf', 'on')
    a.L('off'); a.br('bsr', 'unins'); W(0x0009)
    a.L('ret'); W(0x4F26, 0x000B, 0x0009)
    # ---- unins ----
    a.L('unins'); a.ld(1, LIST); a.ld(3, 1024)
    a.L('ul'); W(0x6011, exw(0, 0)); a.ld(2, 0x8000); W(0x3020); a.br('bt', 'uret')
    a.ld(2, 0x5000); W(0x3020); a.br('bf', 'unx')
    W(0x8511, exw(0, 0)); a.ld(2, OWNL); W(0x3020); a.br('bf', 'unx')
    a.ld(0, 0x8000); W(0x2101); a.br('bra', 'uret'); W(0x0009)
    a.L('unx'); W(addi(1, 32), dt(3)); a.br('bf', 'ul')
    a.L('uret'); W(0x000B, 0x0009)
    # ---- draw(r1 = 쪽) ----
    a.L('draw')
    W(0x4F22, push(1)); W(*[push(r) for r in range(8, 15)])
    W(0x58F7)
    a.ld(2, BUF); a.ld(3, BSTR * 34 // 4); W(movi(0, 0))
    a.L('cb'); W(0x2202, addi(2, 4), dt(3)); a.br('bf', 'cb')
    a.ld(9, 'pay'); W(0x6992)                                          # r9 = 지금 묶음
    W(0x8596, exw(0, 0), ADD(0, 9))
    W(ldb0(8, 3), exb(0, 10), mov(8, 11), addi(11, 4))
    W(0x2AA8); a.br('bt', 'chd')
    a.L('ch')
    W(ldbp(11, 0), exb(0, 1), shll(1), mov(1, 12), shll2(12), shll(12), ADD(1, 12), ADD(9, 12))
    W(ldbp(11, 0), exb(0, 13))
    W(ldbp(11, 0), exb(0, 0), mov(0, 2), 0xC804); a.br('bt', 'g8')
    a.ld(1, 256 * 18); W(ADD(1, 12))
    a.L('g8')
    W(0xC901, shll8(0), OR(0, 13), addi(13, 8), shlr(2), mov(2, 0), 0xC901, mov(0, 2))
    W(shll2(2), shll2(2), addi(2, 4), movi(3, BSTR), 0x0237, 0x021A)
    a.ld(3, BUF); W(ADD(3, 2), mov(13, 0), shlr2(0), shlr(0), ADD(0, 2))
    W(mov(13, 0), 0xC907, mov(0, 14), movi(3, 6))
    a.L('gp')
    W(ldbp(12, 4), exb(4, 4), ldbp(12, 5), exb(5, 5), ldbp(12, 6), exb(6, 6))
    W(mov(4, 0), shll2(0), shll2(0), mov(5, 1), shlr2(1), shlr2(1))
    a.br('bsr', 'stamp'); W(OR(1, 0))
    W(mov(5, 0), 0xC90F, shll8(0))
    a.br('bsr', 'stamp'); W(OR(6, 0))
    W(dt(3)); a.br('bf', 'gp')
    W(dt(10)); a.br('bf', 'ch')
    a.L('chd')
    # 16비트 RGB 선형: 행 y(nrow*8) × 열 cx(w8) × 8 화소
    W(ldb0(8, 1), exb(0, 9), shll2(9), shll(9))
    a.ld(10, BUF); W(addi(10, BSTR)); a.ld(11, TEX)
    a.L('ry'); W(ldb0(8, 0), exb(0, 13), mov(10, 14))
    a.L('rx'); W(mov(14, 2))
    W(mov(2, 4), addi(4, -BSTR), mov(2, 5), addi(5, BSTR))
    W(ldb(4, 0), ldb(2, 1), OR(1, 0), ldb(5, 1), OR(1, 0), exb(0, 6), shll8(6))
    W(ldb0(4, 1), mov(0, 1), ldb0(2, 1), OR(0, 1), ldb0(5, 1), OR(1, 0), exb(0, 0), OR(0, 6), shll8(6))
    W(ldb0(4, 2), mov(0, 1), ldb0(2, 2), OR(0, 1), ldb0(5, 2), OR(1, 0), exb(0, 0), OR(0, 6))
    W(mov(6, 1), shlr8(1), mov(6, 0), shll(0), shlr8(0), OR(0, 1), mov(6, 0), shlr(0), shlr8(0), OR(0, 1))
    W(ldb0(2, 1), exb(0, 7), 0x6077, AND(0, 1), exb(1, 1))
    W(movi(3, 8))
    a.L('eb'); W(mov(7, 0), 0xC880); a.br('bt', 'e1')
    W(movi(0, -1)); a.br('bra', 'es'); W(0x0009)                       # 흰 글자 0xFFFF
    a.L('e1'); W(mov(1, 0), 0xC880); a.br('bt', 'e0')
    W(movi(0, -128)); a.br('bra', 'es'); W(shll8(0))                   # 검정 테두리 0x8000
    a.L('e0'); W(movi(0, 0))
    a.L('es'); W(0x2B01, addi(11, 2), shll(7), shll(1), dt(3)); a.br('bf', 'eb')
    W(addi(14, 1), dt(13)); a.br('bf', 'rx')
    W(movi(0, BSTR), ADD(0, 10), dt(9)); a.br('bf', 'ry')
    W(*[pop(r) for r in range(14, 7, -1)]); W(pop(1))
    # 명령 칸: SIZE · XA YA (지역 좌표 (160,112) 기준, 아래 가운데, 바닥 8px 여유)
    W(ldb0(1, 0), exb(0, 7), ldb0(1, 1), exb(0, 5))                   # r7 = w8 · r5 = nrow
    a.ld(2, 'cmd')
    W(mov(7, 0), shll8(0), mov(5, 6), shll2(6), shll(6), OR(6, 0), 0x8125)          # SIZE = w8<<8 | nrow*8
    W(mov(7, 0), shll2(0), 0x600B, 0x8126)                                           # XA = −w8*4
    W(mov(5, 0), shll2(0), shll(0)); W(movi(6, 104), 0x3608, mov(6, 0), 0x8127)      # YA = 104 − nrow*8
    W(0x4F26, 0x000B, 0x0009)
    # ---- stamp ----
    a.L('stamp')
    W(shll8(0), shll2(0), shll2(0), mov(14, 1), 0x2118); a.br('bt', 'sd')
    a.L('sl'); W(shlr(0), dt(1)); a.br('bf', 'sl')
    a.L('sd'); W(mov(0, 7), shlr16(0), ldb(2, 1), OR(1, 0), stb(0, 2))
    W(mov(7, 1), shlr8(1), ldb0(2, 1), OR(1, 0), stb0(2, 1))
    W(ldb0(2, 2), OR(7, 0), stb0(2, 2), 0x000B, addi(2, BSTR))
    code = a.build(); assert len(code) <= DATA - RES, len(code)
    return code + bytes(DATA - RES - len(code)) + data, a.lab


def build(s0_0, s0_1, sub_blob):
    """→ (새 S0_0, 새 S0_1, 라벨)"""
    res, lab = assemble()
    s0 = bytearray(s0_0)
    assert struct.unpack_from('>I', s0, VBI_LIT - 0x06020000)[0] == VBI
    struct.pack_into('>I', s0, VBI_LIT - 0x06020000, lab['vbi'])
    pad = RES - 0x00200000
    assert len(s0_1) <= pad, (len(s0_1), pad)
    blob = res + bytes(TAB - RES - len(res)) + sub_blob
    assert RES + len(blob) <= END, ('상주 자료가 0x250000 을 넘음', hex(RES + len(blob)))
    return bytes(s0), s0_1 + bytes(pad - len(s0_1)) + blob, lab
