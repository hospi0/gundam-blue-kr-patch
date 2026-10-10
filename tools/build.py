# -*- coding: utf-8 -*-
r"""건담 외전 I 빌드(2026-10-10 PoC) — 음성 자막 훅 + 자막 자료.
  ① S0_0.BIN: VBI 등록 리터럴 → 우리 감싸개(hook.build)
  ② S0_1.BIN: 0x44800 까지 0 채움 + 훅 코드 + 자막 표·묶음(subs.blob) → 하위 RAM 0x00244800 에 상주
  ③ 디스크: iso.patch(트랙 01 크기 그대로, 늘어난 S0_1 은 뒤 빈 자리로) → work/out/
  python tools/build.py [--write]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc, hook, iso, subs

OUT = os.path.join(ROOT, 'work', 'out', 'Mobile Suit Gundam Side Story I - Senritsu no Blue (Japan) (Track 01).bin')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sb, info = subs.blob(hook.TAB)
    s0, s1, lab = hook.build(disc.read('/S0_0.BIN'), disc.read('/S0_1.BIN'), sb)
    print('① 자막 묶음 %s · 상주 끝 %s' % (info, hex(hook.TAB + len(sb))))
    print('② S0_1 %d B(원래 %d) · S0_0 VBI → %s' % (len(s1), len(disc.read('/S0_1.BIN')), hex(lab['vbi'])))
    if '--write' in sys.argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        iso.patch(OUT, {'/S0_0.BIN': s0, '/S0_1.BIN': s1})


if __name__ == '__main__':
    main()
