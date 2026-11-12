"""Free voiceover with Kokoro (Apache-2.0, commercial use allowed). Channel voice: am_liam, speed 1.0.

Each beat (one full spoken line) is generated in ONE call and never cut or spliced, so the voice flows
naturally. Inserting silence inside a line made the voice sound like it was breaking; generating tiny
sentences on their own made it drag. Beats are joined with a short pause.

Returns the 48 kHz WAV path, a list of (start, end) per beat, an estimated (word, start, end) list per beat
(used for captions and for scenes that start mid-beat), and the total length.
"""
import os, re, subprocess, urllib.request
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.join(HERE, "models"))
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
SR = 24000


def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for f in FILES:
        p = os.path.join(MODEL_DIR, f)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print("downloading", f)
            try:
                urllib.request.urlretrieve(BASE + f, p)
            except Exception:  # some sandboxes only allow curl through their proxy
                subprocess.run(["curl", "-sSL", "-o", p, BASE + f], check=True)
    return [os.path.join(MODEL_DIR, f) for f in FILES]


def word_weights(k, words, lang):
    """rough spoken length of each word: phoneme count, plus a beat for punctuation"""
    out = []
    for w in words:
        try:
            ph = k.tokenizer.phonemize(re.sub(r"[^\w'$%.,?!-]", " ", w), lang)
        except Exception:
            ph = w
        n = sum(1 for c in ph if c.isalpha() or c in "ɚɪʊəɑɔæʌɛŋθðʃʒɹɾʔː") or len(w)
        n += 3 * sum(w.endswith(c) for c in ".?!") + 1.5 * w.endswith(",")
        out.append(n)
    return out


def synth(phrases, out_wav, voice="am_liam", speed=1.0, lead=0.15, tail=0.6):
    """phrases: list of dicts with 'say' and optional 'pause' (seconds of silence BEFORE the phrase)."""
    from kokoro_onnx import Kokoro
    k = Kokoro(*ensure_model())
    lang = "en-gb" if voice.startswith("b") else "en-us"
    chunks, times, words, t = [np.zeros(int(lead * SR), np.float32)], [], [], lead
    for i, ph in enumerate(phrases):
        if i:
            gap = float(ph.get("pause", 0.45))
            chunks.append(np.zeros(int(gap * SR), np.float32)); t += gap
        a, sr = k.create(ph["say"], voice=voice, speed=float(ph.get("speed", speed)), lang=lang)
        a = np.asarray(a, np.float32)
        nz = np.where(np.abs(a) > 0.01 * np.abs(a).max())[0]
        a = a[max(0, nz[0] - 600):min(len(a), nz[-1] + 1200)]          # trim silence, keep soft edges
        d = len(a) / SR
        ws = ph["say"].split(); wt = word_weights(k, ws, lang); tot = sum(wt); x = t; wl = []
        for w, n in zip(ws, wt):
            wl.append((w, round(x, 3), round(x + d * n / tot, 3))); x += d * n / tot
        chunks.append(a); times.append((round(t, 3), round(t + d, 3))); words.append(wl); t += d
    chunks.append(np.zeros(int(tail * SR), np.float32))
    y = np.concatenate(chunks)
    raw = out_wav + ".raw.wav"
    sf.write(raw, y / np.abs(y).max() * 0.89, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "pcm_s16le", out_wav], check=True)
    os.remove(raw)
    return out_wav, times, words, len(y) / SR
