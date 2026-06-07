import os
import cv2
import time
import math
import numpy as np
from app.shared.hud_manager import (
    hud_manager
)
from app.models.hologram_panel import (
    HologramPanel
)

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


# ==========================================================================
#  PANEL STATE
# ==========================================================================

# ==========================================================================
#  RENDERER
# ==========================================================================
class HologramRenderer:

    FONT = cv2.FONT_HERSHEY_DUPLEX   # fallback only

    def __init__(self, font_path=None):
        self.start_time = time.time()

        # palette (BGR)
        self.NAVY  = (42, 20, 8)
        self.BLUE  = (255, 180, 40)
        self.SOFT  = (255, 210, 110)
        self.CYAN  = (255, 235, 150)
        self.HOT   = (255, 245, 190)
        self.WHITE = (255, 255, 255)

        # 3D / placement
        self.MARGIN = 46
        self.GLASS_OPACITY = 0.80
        self.REF_FACE_W = 220.0
        self.DEPTH_MIN, self.DEPTH_MAX = 0.6, 1.8
        self.TILT_YAW = 0.08
        self.TILT_PITCH = 0.03
        self.BASE_YAW = 0.10
        self.GLOW_GAIN = 0.35

        # font setup (TTF via PIL if available, Hershey as fallback)
        self._font_cache = {}
        self._init_font(font_path)

    # ----------------------------------------------------------------------
    #  FONT
    # ----------------------------------------------------------------------
    def _init_font(self, font_path):
        candidates = []
        if font_path:
            candidates.append(font_path)
        candidates += [
            # macOS (user's platform)
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Avenir.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # Windows
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        self._font_path = None
        if not _HAS_PIL:
            return
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    ImageFont.truetype(p, 20)   # sanity check it loads
                    self._font_path = p
                    return
                except Exception:
                    continue

    def _get_font(self, size_px):
        if not self._font_path:
            return None
        key = max(8, int(size_px))
        f = self._font_cache.get(key)
        if f is None:
            try:
                f = ImageFont.truetype(self._font_path, key)
            except Exception:
                f = False
            self._font_cache[key] = f
        return f if f else None

    def _char_w(self, font, ch, size_px):
        if ch == " ":
            return int(size_px * 0.32)
        try:
            return int(font.getlength(ch))
        except Exception:
            b = font.getbbox(ch)
            return b[2] - b[0]

    def _measure_text(self, text, size_px, spacing=0):
        f = self._get_font(size_px)
        if f is None:
            return 0
        if spacing <= 0:
            try:
                return int(f.getlength(text))
            except Exception:
                b = f.getbbox(text)
                return b[2] - b[0]
        return max(0, sum(self._char_w(f, c, size_px) + spacing for c in text) - spacing)

    def _fit_size(self, text, max_w, target_px, min_px=12, spacing=0):
        if not text or not self._font_path:
            return target_px
        size = target_px
        while size > min_px:
            if self._measure_text(text, size, spacing) <= max_w:
                return size
            size -= 1
        return min_px

    def _wrap_text(self, text, size_px, max_w, spacing=0):
        """Greedy word-wrap into lines that each fit within max_w.
        A single word longer than max_w is left on its own line (the caller
        shrinks the font / the panel grows to absorb it)."""
        words = (text or "").split()
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if self._measure_text(trial, size_px, spacing) <= max_w:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    # ----------------------------------------------------------------------
    #  BATCHED PIL TEXT RENDER (one BGR<->RGB conversion per panel)
    # ----------------------------------------------------------------------
    def _draw_texts(self, solid, glow, jobs):
        if not jobs:
            return
        if not self._font_path:
            # Hershey fallback
            for j in jobs:
                sc = j["size"] / 30.0
                org = (int(j["x"]), int(j["y"] + j["size"] * 0.8))   # baseline
                cv2.putText(glow, j["text"], org, self.FONT, sc,
                            self._scaled(self.HOT, j["gk"]), 3, cv2.LINE_AA)
                cv2.putText(solid, j["text"], org, self.FONT, sc, j["color"], 2, cv2.LINE_AA)
            return

        pil_s = Image.fromarray(cv2.cvtColor(solid, cv2.COLOR_BGR2RGB))
        pil_g = Image.fromarray(cv2.cvtColor(glow, cv2.COLOR_BGR2RGB))
        ds = ImageDraw.Draw(pil_s)
        dg = ImageDraw.Draw(pil_g)

        for j in jobs:
            font = self._get_font(j["size"])
            if font is None:
                continue
            col = (j["color"][2], j["color"][1], j["color"][0])
            gk = j["gk"]
            glow_rgb = tuple(min(255, int(c * gk)) for c in (self.HOT[2], self.HOT[1], self.HOT[0]))
            x, y = int(j["x"]), int(j["y"])
            sp = j.get("spacing", 0)
            bold = j.get("bold", False)
            if sp > 0:
                for ch in j["text"]:
                    if ch == " ":
                        x += self._char_w(font, ch, j["size"]) + sp
                        continue
                    dg.text((x, y), ch, font=font, fill=glow_rgb,
                            stroke_width=3, stroke_fill=glow_rgb)
                    if bold:
                        ds.text((x, y), ch, font=font, fill=col, stroke_width=1, stroke_fill=col)
                    else:
                        ds.text((x, y), ch, font=font, fill=col)
                    x += self._char_w(font, ch, j["size"]) + sp
            else:
                dg.text((x, y), j["text"], font=font, fill=glow_rgb,
                        stroke_width=3, stroke_fill=glow_rgb)
                if bold:
                    ds.text((x, y), j["text"], font=font, fill=col, stroke_width=1, stroke_fill=col)
                else:
                    ds.text((x, y), j["text"], font=font, fill=col)

        solid[:] = cv2.cvtColor(np.array(pil_s), cv2.COLOR_RGB2BGR)
        glow[:] = cv2.cvtColor(np.array(pil_g), cv2.COLOR_RGB2BGR)

    # ----------------------------------------------------------------------
    #  PIPELINE
    # ----------------------------------------------------------------------
    @staticmethod
    def _ease(t):
        t = max(0.0, min(1.0, t))
        return 1 - (1 - t) ** 3

    def _bloom_layer(self, src, intensity=1.0):
        tight = cv2.GaussianBlur(src, (0, 0), 2.5)
        wide = cv2.GaussianBlur(src, (0, 0), 11)
        b = cv2.addWeighted(tight, 0.8, wide, 0.95, 0)
        if intensity != 1.0:
            b = np.clip(b.astype(np.float32) * intensity, 0, 255).astype(np.uint8)
        return b

    @staticmethod
    def _scaled(color, k):
        return tuple(int(min(255, c * k)) for c in color)

    @staticmethod
    def _cut_corner_poly(x1, y1, x2, y2, cut):
        """Octagonal rectangle: corners shaved off at 45° by `cut` pixels."""
        return np.array([
            [x1 + cut, y1], [x2 - cut, y1],
            [x2, y1 + cut], [x2, y2 - cut],
            [x2 - cut, y2], [x1 + cut, y2],
            [x1, y2 - cut], [x1, y1 + cut],
        ], np.int32)

    def _conduit_flat(self, glow, solid, x1, x2, cy, thick, elapsed, seed):
        cv2.line(solid, (x1, cy), (x2, cy), self.HOT, 2, cv2.LINE_AA)
        cv2.rectangle(glow, (x1, cy - thick // 2), (x2, cy + thick // 2), self.BLUE, -1)
        rng = np.random.default_rng(abs(hash(seed)) % (2 ** 32))
        x = x1 + rng.integers(10, 40)
        while x < x2 - 20:
            yo = int(rng.integers(-thick // 2 + 4, thick // 2 - 4))
            seg = int(rng.integers(16, 64))
            cv2.line(glow, (x, cy + yo), (x + seg, cy + yo), self.HOT, 1, cv2.LINE_AA)
            cv2.rectangle(glow, (x - 2, cy - 2), (x + 2, cy + 2), self.WHITE, -1)
            x += seg + int(rng.integers(8, 24))
        cv2.line(glow, (x1, cy), (x2, cy), self.HOT, 2, cv2.LINE_AA)
        pulse = int((elapsed * 260) % (x2 - x1 + 240)) - 120 + x1
        cv2.line(glow, (pulse, cy - thick // 2), (pulse, cy + thick // 2),
                 self.WHITE, 4, cv2.LINE_AA)

    # ---- decor (incl. NEW right-side outer details) --------------------
    def _decor_flat(self, solid, glow, x1, y1, x2, y2):
        pw, ph = x2 - x1, y2 - y1
        L = int(min(pw, ph) * 0.09)
        tk = max(2, int(min(pw, ph) * 0.010))

        # clean inner corner brackets on all four corners
        for cx, cy, sx, sy in [(x1, y1, 1, 1), (x2, y1, -1, 1),
                               (x1, y2, 1, -1), (x2, y2, -1, -1)]:
            for layer in (solid, glow):
                cv2.line(layer, (cx + sx * 8, cy), (cx + sx * L, cy), self.HOT, tk, cv2.LINE_AA)
                cv2.line(layer, (cx, cy + sy * 8), (cx, cy + sy * L), self.HOT, tk, cv2.LINE_AA)

        # left-edge tick stack
        for i in range(9):
            ty = int(y1 + ph * 0.34 + i * ph * 0.035)
            cv2.line(solid, (x1 + 14, ty), (x1 + 14 + int(pw * 0.020), ty),
                     self.SOFT, 1, cv2.LINE_AA)

        # bottom-left chevron emblem
        ex, ey = x1 + 16, y2 - 14
        for i in range(3):
            cv2.line(solid, (ex + i * 6, ey), (ex + i * 6 + 9, ey - 11),
                     self.CYAN, 2, cv2.LINE_AA)

        # bright top-left accent bar
        ax1, ax2 = x1 + int(pw * 0.10), x1 + int(pw * 0.28)
        ay = y1 + int(ph * 0.10)
        cv2.line(solid, (ax1, ay), (ax2, ay), self.WHITE, 2, cv2.LINE_AA)
        cv2.line(glow, (ax1, ay), (ax2, ay), self.HOT, 3, cv2.LINE_AA)

        # ================================================================
        #  Right-side outer marks + bottom-right diagonal hatch
        # ================================================================
        # dot stack on the outer right edge
        for frac in (0.30, 0.42, 0.54, 0.66):
            dy = int(y1 + ph * frac)
            cv2.circle(solid, (x2 + 12, dy), 2, self.SOFT, -1, cv2.LINE_AA)
            cv2.circle(glow, (x2 + 12, dy), 2, self._scaled(self.HOT, 0.5), -1, cv2.LINE_AA)

        # short horizontal "fins" extending right
        for frac in (0.22, 0.78):
            fy = int(y1 + ph * frac)
            cv2.line(solid, (x2 + 5, fy), (x2 + 18, fy), self.CYAN, 1, cv2.LINE_AA)
            cv2.line(glow, (x2 + 5, fy), (x2 + 18, fy), self.HOT, 1, cv2.LINE_AA)

        # diagonal hatch pattern outside the bottom-right corner (warning-tape feel)
        hatch_count = 5
        hatch_spacing = max(4, int(min(pw, ph) * 0.012))
        hatch_len = max(10, int(min(pw, ph) * 0.035))
        for i in range(hatch_count):
            base_x = x2 + 6 + i * hatch_spacing
            base_y = y2 + 6 + i * hatch_spacing
            cv2.line(solid, (base_x, base_y - hatch_len),
                     (base_x + hatch_len, base_y), self.CYAN, 2, cv2.LINE_AA)
            cv2.line(glow, (base_x, base_y - hatch_len),
                     (base_x + hatch_len, base_y), self._scaled(self.HOT, 0.45), 1, cv2.LINE_AA)

    # ---- button shape only; the label is drawn later via PIL -----------
    def _button_box(self, solid, glow, x1, y1, x2, y2, active, pulse):
        bw, bh = x2 - x1, y2 - y1
        if bw <= 0 or bh <= 0:
            return
        cut = min(14, max(6, bw // 9))   # scale chamfer with button width
        front = np.array([[x1 + cut, y1], [x2 - cut, y1], [x2, y2], [x1, y2]], np.int32)
        cv2.fillPoly(solid, [front], self._scaled(self.NAVY, 0.5))
        gk = (1.0 + 0.3 * pulse) if active else 0.5
        cv2.polylines(glow, [front], True,
                      self._scaled(self.HOT if active else self.BLUE, gk),
                      4 if active else 3, cv2.LINE_AA)
        cv2.polylines(solid, [front], True,
                      self.WHITE if active else self.SOFT, 2, cv2.LINE_AA)
        inner = np.array([[x1 + cut + 5, y1 + 5], [x2 - cut - 5, y1 + 5],
                          [x2 - 5, y2 - 5], [x1 + 5, y2 - 5]], np.int32)
        cv2.polylines(solid, [inner], True, self.BLUE, 1, cv2.LINE_AA)

    # ---- compose the flat layers --------------------------------------
    def _compose_flat(self, panel, pw, ph, elapsed):
        m = self.MARGIN
        CW, CH = pw + 2 * m, ph + 2 * m
        solid = np.zeros((CH, CW, 3), np.uint8)
        glow = np.zeros((CH, CW, 3), np.uint8)
        mask = np.zeros((CH, CW), np.uint8)
        x1, y1, x2, y2 = m, m, m + pw, m + ph

        # cut size for the octagonal frame -- proportional to panel size
        cut_main = max(8, int(min(pw, ph) * 0.030))

        # glass (octagonal mask so the panel itself reads as cut-corner)
        grad = np.linspace(1.25, 0.65, ph, dtype=np.float32)[:, None, None]
        glass = np.clip(np.full((ph, pw, 3), self.NAVY, np.float32) * grad, 0, 255).astype(np.uint8)
        solid[y1:y2, x1:x2] = glass
        cv2.fillPoly(mask, [self._cut_corner_poly(x1, y1, x2, y2, cut_main + 4)], 255)

        # faint inner grid
        step = max(26, pw // 16)
        for gx in range(x1 + step, x2 - 6, step):
            cv2.line(glow, (gx, y1 + 8), (gx, y2 - 8), self._scaled(self.BLUE, 0.10), 1, cv2.LINE_AA)
        for gy in range(y1 + step, y2 - 6, step):
            cv2.line(glow, (x1 + 8, gy), (x2 - 8, gy), self._scaled(self.BLUE, 0.10), 1, cv2.LINE_AA)

        # diagonal haze
        rng = np.random.default_rng(7)
        for _ in range(14):
            sx, sy = int(rng.integers(x1, x2)), int(rng.integers(y1, y2))
            ln = int(rng.integers(40, 140))
            cv2.line(glow, (sx, sy), (sx + ln, sy + ln // 2),
                     self._scaled(self.BLUE, 0.18), 1, cv2.LINE_AA)

        # main double frame -- cut-corner octagonal
        outer_poly = self._cut_corner_poly(x1 + 5, y1 + 5, x2 - 5, y2 - 5, cut_main)
        inner_poly = self._cut_corner_poly(x1 + 12, y1 + 12, x2 - 12, y2 - 12, max(4, cut_main - 4))
        cv2.polylines(solid, [outer_poly], True, self.CYAN, 2, cv2.LINE_AA)
        cv2.polylines(solid, [inner_poly], True, self.SOFT, 1, cv2.LINE_AA)
        cv2.polylines(glow, [outer_poly], True, self.HOT, 3, cv2.LINE_AA)

        # main-frame cut-corner: just a bright diagonal accent (no fill --
        # the glowing triangles belong on the outer frame, added below)
        mfx1, mfy1 = x1 + 5, y1 + 5
        mfx2, mfy2 = x2 - 5, y2 - 5
        for cx, cy, sx, sy in [(mfx1, mfy1, 1, 1), (mfx2, mfy1, -1, 1),
                               (mfx1, mfy2, 1, -1), (mfx2, mfy2, -1, -1)]:
            p1 = (cx + sx * cut_main, cy)
            p2 = (cx, cy + sy * cut_main)
            cv2.line(glow, p1, p2, self.HOT, 3, cv2.LINE_AA)
            cv2.line(solid, p1, p2, self.HOT, 1, cv2.LINE_AA)

        # ================================================================
        #  OUTER thin frame: two open polylines (top + bottom gaps),
        #  each with an inward dent on its side (left/right).
        # ================================================================
        out_off = max(10, int(min(pw, ph) * 0.028))
        oc = cut_main + 2                               # small outer cut (delicate corners)
        ox1, oy1 = x1 - out_off, y1 - out_off
        ox2, oy2 = x2 + out_off, y2 + out_off
        opw, oph = ox2 - ox1, oy2 - oy1

        gap_half = max(int(opw * 0.10), 24)             # half-width of the top/bottom gap
        cx_mid = ox1 + opw // 2
        gap_lx, gap_rx = cx_mid - gap_half, cx_mid + gap_half

        dent_d = max(6, int(min(pw, ph) * 0.025))       # depth of the dent (inward)
        dent_hh = max(int(oph * 0.08), 14)              # half-height of the dent
        cy_mid = oy1 + oph // 2
        dent_ty, dent_by = cy_mid - dent_hh, cy_mid + dent_hh

        # right-side path: top gap -> right edge with dent -> bottom gap
        seg_right = np.array([
            (gap_rx, oy1),
            (ox2 - oc, oy1), (ox2, oy1 + oc),           # top-right cut
            (ox2, dent_ty),
            (ox2 - dent_d, dent_ty),
            (ox2 - dent_d, dent_by),                    # inward dent
            (ox2, dent_by),
            (ox2, oy2 - oc), (ox2 - oc, oy2),           # bottom-right cut
            (gap_rx, oy2),
        ], np.int32)

        # left-side path: bottom gap -> left edge with dent -> top gap
        seg_left = np.array([
            (gap_lx, oy2),
            (ox1 + oc, oy2), (ox1, oy2 - oc),           # bottom-left cut
            (ox1, dent_by),
            (ox1 + dent_d, dent_by),
            (ox1 + dent_d, dent_ty),                    # inward dent
            (ox1, dent_ty),
            (ox1, oy1 + oc), (ox1 + oc, oy1),           # top-left cut
            (gap_lx, oy1),
        ], np.int32)

        # extend mask along just the lines so they composite over background
        cv2.polylines(mask, [seg_right, seg_left], False, 255, 3, cv2.LINE_AA)
        cv2.polylines(solid, [seg_right, seg_left], False, self.SOFT, 1, cv2.LINE_AA)
        # MUCH lighter glow halo around the outer frame for a thin, delicate look
        cv2.polylines(glow, [seg_right, seg_left], False, self._scaled(self.HOT, 0.18), 1, cv2.LINE_AA)

        # ---- small filled glowing triangles at the OUTER frame's 4 cut corners ----
        for cx, cy, sx, sy in [(ox1, oy1, 1, 1), (ox2, oy1, -1, 1),
                               (ox1, oy2, 1, -1), (ox2, oy2, -1, -1)]:
            p1 = (cx + sx * oc, cy)
            p2 = (cx, cy + sy * oc)
            tri = np.array([(cx, cy), p1, p2], np.int32)
            cv2.fillPoly(mask, [tri], 255)
            cv2.fillPoly(solid, [tri], self.HOT)
            cv2.fillPoly(glow, [tri], self.HOT)
            # thin diagonal edge (was 4)
            cv2.line(glow, p1, p2, self.WHITE, 2, cv2.LINE_AA)

        # ---- thin glowing vertical line inside each side dent ----
        for inner_x in (ox2 - dent_d, ox1 + dent_d):
            cv2.line(mask, (inner_x, dent_ty + 4), (inner_x, dent_by - 4), 255, 2, cv2.LINE_AA)
            cv2.line(solid, (inner_x, dent_ty + 4), (inner_x, dent_by - 4), self.HOT, 1, cv2.LINE_AA)
            cv2.line(glow, (inner_x, dent_ty + 4), (inner_x, dent_by - 4), self.WHITE, 2, cv2.LINE_AA)

        # decor (now includes right-side outer details)
        self._decor_flat(solid, glow, x1, y1, x2, y2)

        # ---- collect text jobs to render in a single PIL pass ----------
        text_jobs = []

        if panel.title:
            tgt = int(ph * 0.13)
            spacing = max(1, int(tgt * 0.10))
            tgt = self._fit_size(panel.title, int(pw * 0.74), tgt, spacing=spacing)
            spacing = max(1, int(tgt * 0.10))
            tw = self._measure_text(panel.title, tgt, spacing) or int(tgt * 0.55 * len(panel.title))

            # short centered divider above the title
            cx_mid = x1 + pw // 2
            div_w = max(int(pw * 0.10), int(tw * 0.30))
            cv2.line(solid, (cx_mid - div_w, y1 + int(ph * 0.17)),
                     (cx_mid + div_w, y1 + int(ph * 0.17)), self.WHITE, 1, cv2.LINE_AA)

            text_jobs.append({
                "text": panel.title,
                "x": x1 + (pw - tw) // 2,
                "y": y1 + int(ph * 0.24),
                "size": tgt, "color": self.CYAN, "gk": 0.6, "spacing": spacing,
                "bold": True,
            })

        if panel.message:
            # Word-wrap + auto-shrink so long replies fit the panel instead of
            # spilling past the border. Leave room for option buttons if present.
            max_w = int(pw * 0.84)
            msg_top = y1 + int(ph * 0.36)
            msg_bottom = (y2 - int(ph * 0.30)) if panel.options else (y2 - int(ph * 0.12))
            avail_h = max(int(ph * 0.16), msg_bottom - msg_top)

            size = int(ph * 0.085)
            min_size = max(10, int(ph * 0.045))
            lines = self._wrap_text(panel.message, size, max_w)

            while size > min_size and len(lines) * int(size * 1.25) > avail_h:
                size -= 1
                lines = self._wrap_text(panel.message, size, max_w)

            line_h = int(size * 1.25)

            # Still too tall at the smallest size -> clip and add an ellipsis.
            max_lines = max(1, avail_h // line_h)
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines[-1] = (lines[-1].rstrip() + " ...").strip()

            total_h = len(lines) * line_h
            start_y = msg_top + max(0, (avail_h - total_h) // 2)

            for i, line in enumerate(lines):
                lw = self._measure_text(line, size) or int(size * 0.55 * len(line))
                text_jobs.append({
                    "text": line,
                    "x": x1 + (pw - lw) // 2,
                    "y": start_y + i * line_h,
                    "size": size, "color": self.SOFT, "gk": 0.35, "spacing": 0,
                })

        if panel.options:
            n = len(panel.options)
            gap = int(pw * 0.05)
            bh = max(32, int(ph * 0.17))

            labels = [str(opt) for opt in panel.options]
            target_size = max(13, min(int(bh * 0.42), 30))
            pad_h = max(14, int(bh * 0.50))

            def measure_all(size):
                return [self._measure_text(l, size) or int(size * 0.6 * len(l)) for l in labels]

            label_ws = measure_all(target_size)
            btn_ws = [lw + pad_h * 2 for lw in label_ws]
            total_w = sum(btn_ws) + gap * (n - 1)

            max_total = int(pw * 0.88)
            while target_size > 10 and total_w > max_total:
                target_size -= 1
                pad_h = max(12, int(bh * 0.42))
                label_ws = measure_all(target_size)
                btn_ws = [lw + pad_h * 2 for lw in label_ws]
                total_w = sum(btn_ws) + gap * (n - 1)

            bx = x1 + (pw - total_w) // 2
            by = y2 - int(ph * 0.13) - bh
            pulse = 0.5 + 0.5 * math.sin(elapsed * 6.0)
            for i, (label, btn_w, lw) in enumerate(zip(labels, btn_ws, label_ws)):
                active = ( panel.selected_index is not None and i == panel.selected_index)
                self._button_box(solid, glow, bx, by, bx + btn_w, by + bh, active, pulse)
                text_jobs.append({
                    "text": label,
                    "x": bx + (btn_w - lw) // 2,
                    "y": by + (bh - target_size) // 2 - int(target_size * 0.10),
                    "size": target_size, "color": self.WHITE,
                    "gk": 0.85 if active else 0.35, "spacing": 0,
                    "bold": active,
                })
                bx += btn_w + gap

        # conduits (drawn AFTER text-job collection but BEFORE PIL pass)
        self._conduit_flat(glow, solid, x1 + 26, x2 - 26, y1 - 2, 22, elapsed, panel.key + "T")
        self._conduit_flat(glow, solid, x1 + 26, x2 - 26, y2 + 2, 22, elapsed, panel.key + "B")

        # ---- single PIL conversion pass for all text -------------------
        self._draw_texts(solid, glow, text_jobs)

        return solid, mask, self._bloom_layer(glow, 1.0), CW, CH

    # ---- 3D placement (unchanged) --------------------------------------
    def _project_quad(self, cx, cy, w, h, yaw, pitch):
        f = max(w, h) * 1.6
        cyw, syw = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        out = []
        for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
            xr = x * cyw
            z = x * syw
            yr = y * cp
            z += y * sp
            s = f / (f + z)
            out.append([cx + xr * s, cy + yr * s])
        return np.float32(out)

    def _place_quad(self, frame, panel, face_box, CW, CH, anim):
        H, W = frame.shape[:2]
        if face_box is not None:
            fx, fy, fw, fh = [float(v) for v in face_box]
            depth = float(np.clip(fw / self.REF_FACE_W, self.DEPTH_MIN, self.DEPTH_MAX))
            fcx, fcy = fx + fw / 2, fy + fh / 2
        else:
            fw = W * 0.22
            fx, fy, fh = W * 0.5 - fw / 2, H * 0.5, fw
            fcx, fcy = W * 0.5, H * 0.5
            depth = 1.0

        s = 0.85 + 0.15 * self._ease(anim)
        sw = CW * depth * panel.scale_user * s
        sh = CH * depth * panel.scale_user * s
        vis_w = sw * (CW - 2 * self.MARGIN) / CW
        gap = fw * 0.30

        if panel.anchor == "left":
            cx = fx - gap - vis_w / 2
        else:
            cx = fx + fw + gap + vis_w / 2
            if cx + vis_w / 2 > W - 10:
                cx = fx - gap - vis_w / 2
        cx += panel.offset_x * sw
        cy = fcy + panel.offset_y * sh

        elapsed = time.time() - self.start_time
        cx += math.sin(elapsed * 1.2) * 2
        cy += math.cos(elapsed * 1.4) * 1.5

        cx = float(np.clip(cx, sw / 2, W - sw / 2)) if sw < W else W / 2
        cy = float(np.clip(cy, sh / 2, H - sh / 2)) if sh < H else H / 2

        side = 1.0 if cx >= fcx else -1.0
        yaw = (fcx / W - 0.5) * 2 * self.TILT_YAW - side * self.BASE_YAW
        pitch = (fcy / H - 0.5) * 2 * self.TILT_PITCH
        return self._project_quad(cx, cy, sw, sh, yaw, pitch)

    def render_panel(self, frame, panel, face_box, anim):
        H, W = frame.shape[:2]
        pw = max(40, int(W * panel.width_frac))
        ph = max(40, int(H * panel.height_frac))

        solid, mask, glow, CW, CH = self._compose_flat(
            panel, pw, ph, time.time() - self.start_time)
        dst = self._place_quad(frame, panel, face_box, CW, CH, anim)
        src = np.float32([[0, 0], [CW, 0], [CW, CH], [0, CH]])
        Mp = cv2.getPerspectiveTransform(src, dst)

        bx, by, bw, bh = cv2.boundingRect(dst.astype(np.int32))
        bx0, by0 = max(0, bx), max(0, by)
        bx1, by1 = min(W, bx + bw), min(H, by + bh)
        if bx1 - bx0 <= 0 or by1 - by0 <= 0:
            return frame
        shift = np.float32([[1, 0, -bx0], [0, 1, -by0], [0, 0, 1]])
        Mp = shift @ Mp
        ow, oh = bx1 - bx0, by1 - by0

        solid_w = cv2.warpPerspective(solid, Mp, (ow, oh), flags=cv2.INTER_LINEAR)
        mask_w = cv2.warpPerspective(mask, Mp, (ow, oh), flags=cv2.INTER_LINEAR)
        glow_w = cv2.warpPerspective(glow, Mp, (ow, oh), flags=cv2.INTER_LINEAR)

        ease = self._ease(anim)
        a = (cv2.GaussianBlur(mask_w, (0, 0), 1.0).astype(np.float32) / 255.0)
        a *= self.GLASS_OPACITY * ease
        a = a[:, :, None]

        roi = frame[by0:by1, bx0:bx1].astype(np.float32)
        roi = roi * (1 - a) + solid_w.astype(np.float32) * a
        roi = roi + glow_w.astype(np.float32) * ease * self.GLOW_GAIN
        frame[by0:by1, bx0:bx1] = np.clip(roi, 0, 255).astype(np.uint8)
        return frame

    def render(
        self,
        frame,
        face_box=None
    ):

        hud_manager.update()

        for panel in (
            hud_manager.get_active_panels()
        ):

            anim = panel.update()

            if not panel.alive:
                continue

            self.render_panel(
                frame,
                panel,
                face_box,
                anim
            )

        return frame