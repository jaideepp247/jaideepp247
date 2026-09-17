#!/usr/bin/env python3
"""Generates the animated terminal SVGs for the profile README. No deps."""
from pathlib import Path

OUT = Path(__file__).parent

BG, CHROME, BORDER = "#0d1117", "#161b22", "#30363d"
FG, DIM, GREEN, BLUE, YELLOW, RED, PURPLE = "#e6edf3", "#7d8590", "#3fb950", "#58a6ff", "#d29922", "#f85149", "#bc8cff"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
FS, CW, LH = 14, 8.4, 22          # font size, char width, line height
PAD_X, TOP = 20, 52               # left padding, y of first baseline
TYPE_CPS = 0.045                  # seconds per typed char


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Term:
    def __init__(self, width, title):
        self.w, self.title, self.t, self.rows, self.parts, self.n = width, title, 0.4, 0, [], 0

    def _y(self):
        return TOP + self.rows * LH

    def _span(self, x, text, color, bold=False):
        # Padding spaces advance x but are never rendered, so glyphs are never stretched to fill them.
        w = len(text) * CW
        lead = len(text) - len(text.lstrip(" "))
        core = text.strip(" ")
        if not core:
            return "", w
        weight = ' font-weight="600"' if bold else ""
        return (f'<text x="{x + lead * CW:.1f}" y="{self._y()}" fill="{color}"{weight} textLength="{len(core) * CW:.1f}" '
                f'lengthAdjust="spacingAndGlyphs">{esc(core)}</text>'), w

    def prompt(self, cmd, hold=0.35):
        """Types a command after the prompt, one char at a time."""
        x = PAD_X
        s, w = self._span(x, "jai@prod", GREEN, True); self.parts.append(s); x += w
        s, w = self._span(x, ":", FG); self.parts.append(s); x += w
        s, w = self._span(x, "~", BLUE, True); self.parts.append(s); x += w
        s, w = self._span(x, "$ ", FG); self.parts.append(s); x += w
        self.t += 0.3
        cid = f"c{self.n}"; self.n += 1
        total = len(cmd) * CW
        dur = len(cmd) * TYPE_CPS
        vals = ";".join(f"{i * CW:.1f}" for i in range(len(cmd) + 1))
        self.parts.append(
            f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{self._y() - 16}" height="{LH}" width="0">'
            f'<animate attributeName="width" values="{vals}" calcMode="discrete" begin="{self.t:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'</rect></clipPath>')
        s, _ = self._span(x, cmd, FG)
        self.parts.append(f'<g clip-path="url(#{cid})">{s}</g>')
        # cursor that rides along while typing, then disappears
        self.parts.append(
            f'<rect x="{x:.1f}" y="{self._y() - 13}" width="{CW:.1f}" height="17" fill="{FG}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.9" begin="{self.t - 0.3:.2f}s" dur="0.01s" fill="freeze"/>'
            f'<animate attributeName="x" values="{vals}" calcMode="discrete" begin="{self.t:.2f}s" dur="{dur:.2f}s" fill="freeze" additive="sum"/>'
            f'<animate attributeName="opacity" values="0.9;0" begin="{self.t + dur + hold:.2f}s" dur="0.01s" fill="freeze"/>'
            f'</rect>')
        self.t += dur + hold
        self.rows += 1

    def line(self, segments, delay=0.18):
        """Prints a line at once. segments: list of (text, color[, bold])."""
        x = PAD_X
        gid = f"l{self.n}"; self.n += 1
        inner = []
        for seg in segments:
            text, color = seg[0], seg[1]
            bold = len(seg) > 2 and seg[2]
            s, w = self._span(x, text, color, bold); inner.append(s); x += w
        self.parts.append(
            f'<g opacity="0">{"".join(inner)}'
            f'<animate attributeName="opacity" values="0;1" begin="{self.t:.2f}s" dur="0.05s" fill="freeze"/></g>')
        self.t += delay
        self.rows += 1

    def step(self, label, result="ok", color=GREEN, width=30, delay=0.55):
        """'→ label ......... ok' with dots that fill up before the result lands."""
        gid = f"s{self.n}"; self.n += 1
        x = PAD_X
        s, w = self._span(x, "→ " + label + " ", DIM); head = s; x += w
        dots = "." * max(1, width - len(label) - 2)
        dw = len(dots) * CW
        vals = ";".join(f"{i * CW:.1f}" for i in range(len(dots) + 1))
        s, _ = self._span(x, dots, DIM)
        dots_svg = (f'<clipPath id="{gid}"><rect x="{x:.1f}" y="{self._y() - 16}" height="{LH}" width="0">'
                    f'<animate attributeName="width" values="{vals}" calcMode="discrete" begin="{self.t + 0.05:.2f}s" dur="{delay - 0.15:.2f}s" fill="freeze"/>'
                    f'</rect></clipPath><g clip-path="url(#{gid})">{s}</g>')
        x += dw
        s, _ = self._span(x, " " + result, color, True)
        res_svg = (f'<g opacity="0">{s}<animate attributeName="opacity" values="0;1" '
                   f'begin="{self.t + delay - 0.08:.2f}s" dur="0.05s" fill="freeze"/></g>')
        self.parts.append(
            f'<g opacity="0">{head}<animate attributeName="opacity" values="0;1" begin="{self.t:.2f}s" dur="0.05s" fill="freeze"/></g>'
            + dots_svg + res_svg)
        self.t += delay
        self.rows += 1

    def cursor(self):
        """Resting prompt with a blinking cursor."""
        x = PAD_X
        inner = []
        for text, color, bold in (("jai@prod", GREEN, True), (":", FG, False), ("~", BLUE, True), ("$ ", FG, False)):
            s, w = self._span(x, text, color, bold); inner.append(s); x += w
        self.parts.append(
            f'<g opacity="0">{"".join(inner)}'
            f'<rect x="{x:.1f}" y="{self._y() - 13}" width="{CW:.1f}" height="17" fill="{FG}">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
            f'<animate attributeName="opacity" values="0;1" begin="{self.t:.2f}s" dur="0.05s" fill="freeze"/></g>')
        self.rows += 1

    def blank(self, delay=0.1):
        self.rows += 1; self.t += delay

    def render(self):
        h = TOP + self.rows * LH + 6
        tw = len(self.title) * 7.2
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" viewBox="0 0 {self.w} {h}" font-family="{FONT}" font-size="{FS}" xml:space="preserve">
<rect width="{self.w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M10 0 H{self.w - 10} a10 10 0 0 1 10 10 V34 H0 V10 a10 10 0 0 1 10 -10 Z" fill="{CHROME}"/>
<line x1="0" y1="34" x2="{self.w}" y2="34" stroke="{BORDER}"/>
<circle cx="20" cy="17" r="6" fill="#ff5f57"/><circle cx="40" cy="17" r="6" fill="#febc2e"/><circle cx="60" cy="17" r="6" fill="#28c840"/>
<text x="{self.w / 2 - tw / 2:.1f}" y="21.5" fill="{DIM}" font-size="12" textLength="{tw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(self.title)}</text>
{chr(10).join(self.parts)}
</svg>'''


# ---------- Scene 1: hero session ----------
t = Term(920, "jai-deep — devops — ~")
t.prompt("whoami")
t.line([("jai deep", FG, True), ("   devops engineer · karachi, pk", DIM)])
t.blank()
t.prompt("journalctl -u jai.service -o cat --no-pager")
log = [
    ("lead devops across the org",           "infra · pipelines · security · mentoring"),
    ("100+ apps shipped to production",      "aws · azure · gcp · digitalocean · hetzner · strato"),
    ("hardened 70+ ci/cd pipelines",         "killed long-lived pats · gitleaks · automated rollback"),
    ("frontend cve audit across 200+ repos", "findings + remediation paths routed to owning teams"),
    ("cross-platform deployment framework",  "full stack on linux, windows, macos from one interface"),
    ("devs stopped needing server access",   "pm2 logs, metrics + control · rbac enforced server-side"),
    ("wired an llm reviewer into pr checks", "qodo + gpt-4o, automated first-pass review"),
]
for what, detail in log:
    t.line([(f"{what:<38}", FG, True), (detail, DIM)], delay=0.34)
t.blank()
t.cursor()
(OUT / "hero.svg").write_text(t.render())

# ---------- Scene 2: stack as systemd units ----------
t = Term(920, "systemctl — stack")
t.prompt("systemctl list-units --type=stack")
t.line([("  ", DIM), (f"{'UNIT':<21}", DIM), (f"{'ACTIVE':<9}", DIM), ("PROVIDES", DIM)], delay=0.25)
rows = [
    ("aws.service",        "ec2 · rds · s3 · cloudfront · route53 · alb · asg · vpc · cloudwatch"),
    ("providers.service",  "azure · gcp · digitalocean · hetzner · strato"),
    ("cicd.service",       "github actions · codepipeline · codedeploy · health checks + rollback"),
    ("containers.service", "docker · buildx multi-arch (amd64 · arm64) · ecs · ecr"),
    ("selfhosted.service", "coolify · garage · rustfs · s3-compatible storage on-prem"),
    ("networking.service", "nginx · caddy · cloudflare tunnels · dns · tls + cert automation"),
    ("security.service",   "gitleaks · scoped ci tokens · dependency cve audits"),
    ("automation.service", "bash · powershell · terraform · across linux, windows, macos"),
]
for unit, provides in rows:
    t.line([("● ", GREEN, True), (f"{unit:<21}", FG), (f"{'active':<9}", GREEN), (provides, DIM)], delay=0.16)
t.blank()
t.line([("8 loaded units listed. all active.", DIM)], delay=0.2)
t.cursor()
(OUT / "skills.svg").write_text(t.render())

# ---------- Scene 3: contact ----------
t = Term(920, "contact — ~")
t.prompt("cat ~/.contact")
t.line([("email      ", DIM), ("jaideepp247@gmail.com", BLUE)])
t.line([("linkedin   ", DIM), ("linkedin.com/in/jaideep247", BLUE)])
t.line([("writing    ", DIM), ("dev.to/jaideep247", BLUE)])
t.cursor()
(OUT / "contact.svg").write_text(t.render())

print("wrote hero.svg skills.svg contact.svg")
