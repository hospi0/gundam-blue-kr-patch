# -*- coding: utf-8 -*-
r"""SS_SND.BIN 읽기(2026-10-10)
  머리 0x800: u32 BE [0]=0x800, [1..6]=그룹 표 위치, 0x1C 부터 (오프셋, 크기) 쌍 30개.
  6‥29번 = 음성 스트림 — 16비트 BE PCM 모노 22,050 Hz, 머리 없음. 0‥5 = 소리 은행.
"""
import os, struct
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'work', 'disc', 'SS_SND.BIN')
RATE = 22050
VOICES = range(6, 30)


def table(d=None):
    d = d or open(PATH, 'rb').read()
    w = struct.unpack_from('>512I', d, 0); out = []; i = 0x1C // 4
    while i + 1 < 512 and w[i]:
        out.append((w[i], w[i + 1])); i += 2
    return out


def voice(k, d=None):
    d = d or open(PATH, 'rb').read(); o, s = table(d)[k]
    return d[o:o + s]
