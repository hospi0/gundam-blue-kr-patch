# -*- coding: utf-8 -*-
"""자막 훅 검산(2026-10-10 PoC): 스트림 구조 흉내 → 쪽 고르기·16비트 그림·명령 칸·END 점프·꺼짐"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.append(r'C:\claude\project\burningrangers-kr-patch\tools')
import glyphpack as G
import hook as H, subs, sh2sim as S


def mem(blob):
    m = S.Mem(); m.add(0x06000000, 0x100000); m.add(0x00200000, 0x100000); m.add(0x05C00000, 0x80000)
    m._f(H.RES)[0][H.RES - 0x00200000:H.RES - 0x00200000 + len(blob)] = blob
    return m


def ref_tex(lines):
    w8, nrow, chars = G.layout(lines); px = G.reference(w8, nrow, chars)
    return w8, nrow, b''.join({0: b'\0\0', 1: b'\x80\0', 15: b'\xff\xff'}[int(v)] for v in px.ravel())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    res, lab = H.assemble()
    sb, info = subs.blob(H.TAB)
    blob = res + bytes(H.TAB - H.RES - len(res)) + sb
    ok = True
    for v in ('V25', 'V07'):
        pages = subs.pages_for(subs.POC[v]); k = int(v[1:]) - 6
        for pi in (0, len(pages) - 1):
            t0, t1, lines = pages[pi]; t = int(round(t0 * 60)) + 2
            for listlen in (0, 3):
                m = mem(blob)
                for q in range(listlen): m.w16(H.LIST + 32 * q, 0x0000); m.w16(H.LIST + 32 * q + 8, 0x1234)
                m.w16(H.LIST + 32 * listlen, 0x8000); m.w16(H.LIST + 32 * listlen + 32, 0x4321)
                m.w32(H.STREAM + 0x0C, 3); m.w32(H.STREAM + 4, k); m.w32(H.STREAM + 0x18, (t + H.LEAD) * 735 + 1)
                S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
                X = H.LIST + 32 * listlen; O = H.OWN
                w8, nrow, tex = ref_tex(lines)
                cmd = [m.r16(O + 2 * i) for i in range(8)]
                want = [0, 0, 0xA8, 0, H.TEXA, w8 << 8 | nrow * 8, (-w8 * 4) & 0xFFFF, (104 - nrow * 8) & 0xFFFF]
                got = bytes(m.r8(H.TEX + i) for i in range(len(tex)))
                c = (cmd == want, m.r16(X) == 0x5000 and m.r16(X + 2) == H.OWNL, m.r16(O + 32) == 0x8000,
                     m.r16(X + 32) == 0x4321, got == tex)
                m.w32(H.STREAM + 0x0C, 5); S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
                c += (m.r16(X) == 0x8000,)
                print('%s 쪽%d 게임명령%d: 명령 %s · 점프 %s · 우리END %s · 다음칸 그대로 %s · 그림 %s · 끝나면 END %s  %s' % ((v, pi, listlen) + c + (lines,)))
                if not c[0]: print('   ', [hex(x) for x in cmd], [hex(x) for x in want])
                ok &= all(c)
    # 표에 없는 스트림 = 자막 없음
    m = mem(blob); m.w16(H.LIST, 0x8000); m.w32(H.STREAM + 0x0C, 3); m.w32(H.STREAM + 4, 5); m.w32(H.STREAM + 0x18, 100 * 735)
    S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None}); hit = m.r16(H.LIST) == 0x8000
    print('표에 없는 스트림 = 자막 없음', hit); ok &= hit
    print('코드 %d B · 상주 끝 %s(한계 %s)' % (len(res), hex(H.TAB + len(sb)), hex(H.END)))
    print('결과', '통과' if ok else '실패')


if __name__ == '__main__':
    main()
