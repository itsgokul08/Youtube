#!/usr/bin/env python3
"""Render the LISA "Tarantino" Short (1080x1920) with ffmpeg.

Drop Flow clips into Lisa/Clips as S1.mp4 ... S6.mp4. Any missing clip is
replaced by a labelled placeholder, so the edit always renders.

    python3 Lisa/Edit/render.py
"""
import glob
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../Lisa
CLIPS = os.path.join(ROOT, "Clips")
SFX = os.path.join(ROOT, "SFX")
OUT = os.path.join(ROOT, "Export", "lisa_tarantino_short.mp4")
VO = glob.glob(os.path.join(ROOT, "Voiceover", "*.mp3"))[0]
W, H, FPS = 1080, 1920, 30
FONT = "Liberation Sans"

# VO line timings (seconds), measured from the pauses in the voiceover.
LINES = [
    (0.00, 2.76, "LISA has a hotel full of {r}villains{/} to get through…"),
    (3.37, 5.17, "and a {r}flight{/} she can't miss."),
    (5.79, 9.21, "So why — halfway through the mission —"),
    (9.50, 11.28, "does she stop… to sign a fan's {y}game controller{/}?"),
    (12.53, 14.07, "This is \"Tarantino\" —"),
    (14.39, 18.46, "the lead single from her new EP, {y}Press Play{/}, out October 23rd."),
    (18.92, 21.10, "Every scene plays like a {y}spy film{/}."),
    (21.60, 24.38, "The lyrics name-drop Kill Bill… and Death Proof."),
    (24.78, 27.58, "It's built on purpose. Shot by shot."),
    (28.14, 29.26, "Look at that {y}controller{/} again."),
    (30.10, 32.15, "It's not just any PlayStation controller."),
    (32.55, 34.59, "It's one LISA helped {y}design herself{/}."),
    (35.00, 38.61, "She's not signing a fan's gift. She's signing her {y}own work{/}."),
    (39.02, 41.10, "And it's not the only thing she signs off on."),
    (41.56, 45.01, "In the final scene, she sends a message to her {y}\"favorite director\"{/} —"),
    (45.36, 48.76, "and the video hints that director is somewhere {y}inside the hotel{/}."),
    (49.26, 50.42, "Who that message is for…"),
    (50.86, 51.64, "that's {y}part 2{/}."),
    (52.16, 55.80, "Right now, LISA has a hotel full of {r}villains{/} to get through—"),
]

# Background segments: (start, end, source, kind, clip_offset)
#   kind "clip"   = play the clip from clip_offset
#   kind "freeze" = hold the frame at clip_offset with a slow push-in
#   kind "black"  = plain black card (text comes from the overlay layer)
FREEZE_AT = 3.5  # moment in S2 where the controller is clearest
SEGMENTS = [
    (0.00, 5.79, "S1", "clip", 0),
    (5.79, 9.50, "S2", "clip", 0),
    (9.50, 12.53, "S2", "freeze", FREEZE_AT),
    (12.53, 18.92, None, "black", 0),
    (18.92, 21.60, "S3", "clip", 0),
    (21.60, 24.78, None, "black", 0),
    (24.78, 28.14, "S4", "clip", 0),
    (28.14, 39.02, "S2", "freeze", FREEZE_AT),
    (39.02, 45.36, "S5", "clip", 0),
    (45.36, 55.80, "S6", "clip", 0),
]
END = 55.80

SFX_HITS = (
    [("tick", t) for t in range(0, 6)]
    + [("whoosh", t - 0.2) for t in (5.79, 12.53, 18.92, 21.60, 24.78, 39.02, 45.36)]
    + [("impact", 28.14), ("impact", 32.55), ("impact", 21.70), ("impact", 23.10), ("ping", 41.56)]
    + [("tick", 52.2 + i) for i in range(4)]
)


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def styled(text):
    return (text.replace("{y}", r"{\c&H18C5F5&}").replace("{r}", r"{\c&H2626E0&}")
            .replace("{/}", r"{\c&HFFFFFF&}"))


def build_ass(path):
    ev = []

    def add(start, end, style, text):
        ev.append(f"Dialogue: 0,{ts(start)},{ts(end)},{style},,0,0,0,,{text}")

    for start, end, text in LINES:
        add(start, end + 0.25, "Cap", r"{\fad(60,0)\fscx80\fscy80\t(0,90,\fscx100\fscy100)}" + styled(text))

    # Stakes: boarding card and countdown (also closes the loop at the end).
    for a, b in ((0.0, 5.79), (52.16, END)):
        add(a, b, "Card", r"{\pos(540,330)}FLIGHT: BOARDING")
        if a == 0:
            for t in range(int(b) + 1):
                add(t, min(t + 1, b), "Clock", r"{\pos(540,470)}00:%02d" % (59 - t))
        else:
            # Hold the opening frame's time so the replay looks continuous.
            add(a, b, "Clock", r"{\pos(540,470)}00:59")

    # Big question held on the frozen controller.
    add(9.50, 12.53, "Q", r"{\pos(540,420)\fad(150,0)}WHY STOP TO SIGN THIS?")
    ring = r"{\an7\pos(540,880)\p1\1a&HFF&\3c&H18C5F5&\bord10\shad0}"
    circle = "m -220 0 b -220 -122 -122 -220 0 -220 b 122 -220 220 -122 220 0 b 220 122 122 220 0 220 b -122 220 -220 122 -220 0{\\p0}"
    add(9.50, 12.53, "Q", ring + circle)

    # Title card.
    add(12.53, 18.92, "Title", r"{\pos(540,760)\fad(0,120)\fscx130\fscy130\t(0,200,\fscx100\fscy100)}TARANTINO")
    add(14.39, 18.92, "Sub", r"{\pos(540,900)\fad(150,0)}LISA · PRESS PLAY EP · OCT 23")

    # Film-title slams.
    add(21.70, 24.78, "Slam", r"{\pos(540,700)\fscx160\fscy160\t(0,120,\fscx100\fscy100)}KILL BILL")
    add(23.10, 24.78, "Slam", r"{\pos(540,900)\fscx160\fscy160\t(0,120,\fscx100\fscy100)}DEATH PROOF")

    # Head fake: back on the planted clue.
    add(28.14, 32.55, "Q", r"{\pos(540,420)\fad(120,0)}LOOK AGAIN")
    add(28.14, 39.02, "Q", ring + circle)
    add(32.55, 39.02, "Slam", r"{\pos(540,420)\fs120\fscx170\fscy170\t(0,120,\fscx100\fscy100)}SHE DESIGNED IT")

    # Re-hook: the message.
    add(41.56, 45.36, "Bubble", r"{\pos(540,820)\fad(100,0)\fscx70\fscy70\t(0,120,\fscx100\fscy100)}to my favorite director…")
    add(50.86, 52.16, "Slam", r"{\pos(540,700)\fscx160\fscy160\t(0,120,\fscx100\fscy100)}PART 2")

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,3,2,90,90,560,1
Style: Card,{FONT},64,&H00FFFFFF,&H00FFFFFF,&H002626E0,&H00000000,1,0,0,0,100,100,4,0,3,18,0,5,0,0,0,1
Style: Clock,DejaVu Sans Mono,120,&H002626E0,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,5,0,5,0,0,0,1
Style: Q,{FONT},84,&H0018C5F5,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,6,0,5,0,0,0,1
Style: Title,{FONT},190,&H0018C5F5,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,86,100,6,0,1,0,0,5,0,0,0,1
Style: Sub,{FONT},52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1
Style: Slam,{FONT},150,&H0018C5F5,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,86,100,4,0,1,7,0,5,0,0,0,1
Style: Bubble,{FONT},60,&H00000000,&H00FFFFFF,&H00F0F0F0,&H00000000,1,0,0,0,100,100,0,0,3,28,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as f:
        f.write(head + "\n".join(ev) + "\n")


def find_clip(name):
    hits = glob.glob(os.path.join(CLIPS, name + ".*"))
    return hits[0] if hits else None


def render_segment(i, seg, tmp):
    start, end, src, kind, off = seg
    dur = end - start
    out = os.path.join(tmp, f"seg{i:02d}.mp4")
    fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    clip = find_clip(src) if src else None
    enc = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out]

    if kind == "black":
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0b0b0b:s={W}x{H}:r={FPS}:d={dur:.3f}"] + enc)
    elif clip is None:
        label = f"{src} placeholder - add Lisa/Clips/{src}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x1c1414:s={W}x{H}:r={FPS}:d={dur:.3f}",
             "-vf", f"drawtext=font='{FONT}':text='{label}':fontcolor=0x777777:fontsize=40:x=(w-tw)/2:y=h*0.12"] + enc)
    elif kind == "freeze":
        frames = int(round(dur * FPS))
        zoom = "min(1+0.0009*on,1.25)" if dur < 5 else "min(1+0.0012*on,1.45)"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(off), "-i", clip, "-frames:v", "1", "-vf", fit,
             os.path.join(tmp, f"f{i}.png")])
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", os.path.join(tmp, f"f{i}.png"), "-vf",
             f"zoompan=z='{zoom}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={W}x{H}:fps={FPS}",
             "-frames:v", str(frames)] + enc)
    else:
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(off), "-stream_loop", "-1", "-i", clip, "-t", f"{dur:.3f}",
             "-vf", fit] + enc)
    return out


def main():
    with tempfile.TemporaryDirectory() as tmp:
        segs = [render_segment(i, s, tmp) for i, s in enumerate(SEGMENTS)]
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{p}'\n" for p in segs)
        ass = os.path.join(tmp, "overlay.ass")
        build_ass(ass)

        inputs = ["-f", "concat", "-safe", "0", "-i", lst, "-i", VO]
        mix = ["[1:a]volume=1.0[vo]"]
        labels = ["[vo]"]
        for n, (name, t) in enumerate(SFX_HITS):
            inputs += ["-i", os.path.join(SFX, name + ".wav")]
            ms = int(max(t, 0) * 1000)
            mix.append(f"[{n + 2}:a]adelay={ms}|{ms},volume=0.55[s{n}]")
            labels.append(f"[s{n}]")
        mix.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95[a]")

        vf = (f"[0:v]eq=contrast=1.08:saturation=1.1,noise=alls=6:allf=t,vignette=PI/5,"
              f"subtitles='{ass}'[v]")
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", vf + ";" + ";".join(mix),
             "-map", "[v]", "-map", "[a]", "-t", str(END), "-c:v", "libx264", "-preset", "medium",
             "-crf", "23", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", OUT])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
