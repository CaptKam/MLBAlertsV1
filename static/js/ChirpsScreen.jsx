import React, { useState, useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════════════════
// CHIRP.BET — CHIRPS SCREEN (Modern Redesign)
// Clean hierarchy, subtle depth, purposeful animation
// ═══════════════════════════════════════════════════════════════

// --- Data ---
const ESPN_LOGO = (id) =>
  `https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/${id}.png&h=80&w=80`;

const TEAMS = {
  NYY: { abbr: "NYY", name: "Yankees", color: "#003087", espn: "nyy" },
  BOS: { abbr: "BOS", name: "Red Sox", color: "#BD3039", espn: "bos" },
  LAD: { abbr: "LAD", name: "Dodgers", color: "#005A9C", espn: "lad" },
  SF:  { abbr: "SF",  name: "Giants",  color: "#FD5A1E", espn: "sf" },
  HOU: { abbr: "HOU", name: "Astros",  color: "#002D62", espn: "hou" },
  TEX: { abbr: "TEX", name: "Rangers", color: "#003278", espn: "tex" },
  CHC: { abbr: "CHC", name: "Cubs",    color: "#0E3386", espn: "chc" },
  STL: { abbr: "STL", name: "Cardinals",color: "#C41E3A", espn: "stl" },
  ATL: { abbr: "ATL", name: "Braves",  color: "#CE1141", espn: "atl" },
  PHI: { abbr: "PHI", name: "Phillies", color: "#E81828", espn: "phi" },
};

// --- Design Tokens ---
// Inspired by Linear/Vercel — dark, muted, precise
const t = {
  // Surfaces
  bg:       "#06080C",
  surface:  "#0C1017",
  card:     "#10141C",
  elevated: "#161C28",
  // Borders
  border:       "rgba(255,255,255,0.06)",
  borderSubtle: "rgba(255,255,255,0.04)",
  borderHover:  "rgba(255,255,255,0.10)",
  // Text
  white:     "#F0F4F8",
  primary:   "#D4DCE8",
  secondary: "#8B99AE",
  muted:     "#5C6B82",
  dim:       "#3D4A5C",
  // Accents
  red:    "#EF4444",
  amber:  "#F59E0B",
  blue:   "#3B82F6",
  green:  "#22C55E",
  cyan:   "#06B6D4",
  // Accent backgrounds (very subtle)
  redBg:    "rgba(239,68,68,0.06)",
  amberBg:  "rgba(245,158,11,0.06)",
  blueBg:   "rgba(59,130,246,0.06)",
  greenBg:  "rgba(34,197,94,0.05)",
  // Radius
  r:  14,
  rs: 10,
  // Shadows
  cardShadow: "0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)",
  elevShadow: "0 4px 16px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
};

const fontDisplay = {
  fontFamily: "'Inter','SF Pro Display',-apple-system,system-ui,sans-serif",
};
const fontMono = {
  fontFamily: "'JetBrains Mono','SF Mono','Menlo',monospace",
};

const ordinal = (n) => {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

// --- CSS Injection ---
const CSS_ID = "chirps-v2-css";
const injectCSS = () => {
  if (typeof document === "undefined" || document.getElementById(CSS_ID)) return;
  const el = document.createElement("style");
  el.id = CSS_ID;
  el.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.3s ease-out both; }

    @keyframes pulse-dot {
      0%, 100% { opacity: 1; }
      50%      { opacity: 0.3; }
    }
    .pulse-dot { animation: pulse-dot 2s ease-in-out infinite; }

    @keyframes shimmer {
      0%   { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
    .shimmer {
      background: linear-gradient(90deg,
        rgba(255,255,255,0.03) 25%,
        rgba(255,255,255,0.06) 50%,
        rgba(255,255,255,0.03) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.6s ease infinite;
    }

    @keyframes slide-up {
      from { transform: translateY(100%); }
      to   { transform: translateY(0); }
    }
    .slide-up { animation: slide-up 0.35s cubic-bezier(0.16, 1, 0.3, 1); }

    .hide-scroll::-webkit-scrollbar { display: none; }
    .hide-scroll { scrollbar-width: none; }

    .chirp-card {
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .chirp-card:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.06);
    }

    .tap-target {
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .tap-target:active {
      background: rgba(255,255,255,0.03) !important;
    }
  `;
  document.head.appendChild(el);
};

// ═══════════════════════════════════════
// PRIMITIVES
// ═══════════════════════════════════════

function TeamLogo({ team, size = 28 }) {
  const data = TEAMS[team];
  if (!data) {
    return (
      <div style={{
        width: size, height: size, borderRadius: "50%",
        background: t.elevated, flexShrink: 0,
      }} />
    );
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%", overflow: "hidden",
      flexShrink: 0, background: "rgba(255,255,255,0.05)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <img
        src={ESPN_LOGO(data.espn)}
        alt={data.abbr}
        style={{ width: size * 0.76, height: size * 0.76, objectFit: "contain" }}
        onError={(e) => { e.target.style.display = "none"; }}
      />
    </div>
  );
}

function Diamond({ bases = [false, false, false], size = 40 }) {
  const m = size / 2;
  const d = size * 0.12;
  const pos = [
    { x: size * 0.85, y: m },       // 1st
    { x: m, y: size * 0.15 },       // 2nd
    { x: size * 0.15, y: m },       // 3rd
  ];
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Paths */}
      <polygon
        points={`${m},${size * 0.15} ${size * 0.85},${m} ${m},${size * 0.85} ${size * 0.15},${m}`}
        fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="0.8"
      />
      {/* Home */}
      <rect
        x={m - d / 2} y={size * 0.85 - d / 2} width={d} height={d}
        fill={t.elevated} stroke="rgba(255,255,255,0.12)" strokeWidth="0.6"
        transform={`rotate(45 ${m} ${size * 0.85})`}
      />
      {/* Bases */}
      {pos.map((p, i) => (
        <rect key={i}
          x={p.x - d / 2} y={p.y - d / 2} width={d} height={d}
          fill={bases[i] ? t.amber : t.elevated}
          stroke={bases[i] ? "rgba(245,158,11,0.5)" : "rgba(255,255,255,0.10)"}
          strokeWidth="0.6"
          transform={`rotate(45 ${p.x} ${p.y})`}
        />
      ))}
    </svg>
  );
}

function OutDots({ count = 0 }) {
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          width: 5, height: 5, borderRadius: "50%",
          background: i < count ? t.amber : "rgba(255,255,255,0.08)",
          boxShadow: i < count ? "0 0 4px rgba(245,158,11,0.25)" : "none",
        }} />
      ))}
    </div>
  );
}

function Badge({ label, color = "green", pulse = false }) {
  const colors = { red: t.red, green: t.green, blue: t.blue, amber: t.amber, cyan: t.cyan };
  const c = colors[color] || color;
  return (
    <span className={pulse ? "pulse-dot" : ""} style={{
      display: "inline-flex", alignItems: "center",
      padding: "3px 8px", borderRadius: 6,
      background: `${c}10`, border: `1px solid ${c}18`,
      fontSize: 10, fontWeight: 600, color: c,
      letterSpacing: "0.02em", ...fontDisplay,
    }}>
      {label}
    </span>
  );
}

function Skeleton({ w = "100%", h = 12, r = 6 }) {
  return (
    <div className="shimmer" style={{
      width: w, height: h, borderRadius: r,
      background: "rgba(255,255,255,0.04)",
    }} />
  );
}

// ═══════════════════════════════════════
// CARD COMPONENTS
// ═══════════════════════════════════════

function ChirpCard({ alert, level, expanded, onToggle, onTapLine }) {
  const levelConfig = {
    strong: { color: t.red, label: "STRONG CHIRP", accentBg: t.redBg },
    chirp:  { color: t.amber, label: "CHIRP", accentBg: t.amberBg },
    soft:   { color: t.blue, label: "SOFT CHIRP", accentBg: t.blueBg },
  };
  const cfg = levelConfig[level];
  const a = alert;
  const isLive = a.inn > 0;
  const isExpanded = expanded;

  return (
    <div className="chirp-card fade-in" style={{
      background: t.card,
      border: `1px solid ${t.border}`,
      borderRadius: t.r,
      borderLeft: `3px solid ${cfg.color}`,
      boxShadow: level === "strong"
        ? `0 2px 16px rgba(0,0,0,0.35), 0 0 0 1px ${cfg.color}08`
        : t.cardShadow,
      marginBottom: 12,
      overflow: "hidden",
    }}>
      <div style={{ padding: "16px 16px 0" }}>

        {/* Header: Level + Edge % */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 14,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Badge label={cfg.label} color={level === "strong" ? "red" : level === "chirp" ? "amber" : "blue"} pulse={level === "strong"} />
            <span style={{
              ...fontMono, fontSize: level === "strong" ? 26 : 22,
              fontWeight: 800, color: cfg.color, letterSpacing: "-0.03em",
            }}>
              +{a.edge}%
            </span>
          </div>
          <span style={{ fontSize: 10, color: t.muted, ...fontDisplay }}>{a.time}</span>
        </div>

        {/* Scoreboard */}
        <div style={{
          padding: isLive ? "12px 14px" : "10px 14px",
          background: "rgba(255,255,255,0.02)",
          borderRadius: t.rs,
          border: `1px solid ${t.borderSubtle}`,
          marginBottom: 12,
        }}>
          <div style={{ display: "flex", alignItems: "center" }}>
            {/* Away */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8 }}>
              <TeamLogo team={a.t1} size={isLive ? 28 : 24} />
              <div>
                <span style={{
                  fontSize: 13, fontWeight: 700, color: t.white,
                  ...fontDisplay, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t1]?.abbr}</span>
                <span style={{
                  fontSize: 9, color: t.muted, ...fontDisplay,
                }}>{TEAMS[a.t1]?.name}</span>
              </div>
              {isLive && (
                <span style={{
                  ...fontMono, fontSize: 24, fontWeight: 800, color: t.white,
                  marginLeft: "auto", letterSpacing: "-0.03em",
                }}>{a.s1}</span>
              )}
            </div>

            {/* Center: Diamond or Time */}
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 3, margin: "0 12px", flexShrink: 0,
            }}>
              {isLive ? (
                <>
                  <Diamond bases={a.bases} size={36} />
                  <div style={{ display: "flex", alignItems: "center", gap: 3 }}>
                    <div className="pulse-dot" style={{
                      width: 4, height: 4, borderRadius: "50%", background: t.green,
                    }} />
                    <span style={{
                      fontSize: 9, fontWeight: 700, color: t.green, ...fontDisplay,
                    }}>{a.top ? "\u25B2" : "\u25BC"}{ordinal(a.inn)}</span>
                    <OutDots count={a.outs} />
                  </div>
                </>
              ) : (
                <span style={{
                  fontSize: 11, fontWeight: 600, color: t.muted, ...fontDisplay,
                }}>@ 7:10 PM</span>
              )}
            </div>

            {/* Home */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, flexDirection: "row-reverse" }}>
              <TeamLogo team={a.t2} size={isLive ? 28 : 24} />
              <div style={{ textAlign: "right" }}>
                <span style={{
                  fontSize: 13, fontWeight: 700, color: t.white,
                  ...fontDisplay, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t2]?.abbr}</span>
                <span style={{
                  fontSize: 9, color: t.muted, ...fontDisplay,
                }}>{TEAMS[a.t2]?.name}</span>
              </div>
              {isLive && (
                <span style={{
                  ...fontMono, fontSize: 24, fontWeight: 800, color: t.white,
                  marginRight: "auto", letterSpacing: "-0.03em",
                }}>{a.s2}</span>
              )}
            </div>
          </div>
        </div>

        {/* Matchup Context (batter / pitcher) — only for strong/chirp with live data */}
        {isLive && level !== "soft" && (
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <div style={{
              flex: 1, padding: "8px 10px", borderRadius: 8,
              background: t.blueBg, border: `1px solid rgba(59,130,246,0.08)`,
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.blue, letterSpacing: "0.04em", ...fontDisplay }}>AT BAT</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: t.white, ...fontDisplay, marginTop: 2 }}>{a.bat.name}</div>
              <div style={{ ...fontMono, fontSize: 10, color: t.secondary, marginTop: 1 }}>{a.bat.avg} / {a.bat.hr} HR</div>
            </div>
            <div style={{
              flex: 1, padding: "8px 10px", borderRadius: 8,
              background: t.redBg, border: `1px solid rgba(239,68,68,0.08)`,
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.red, letterSpacing: "0.04em", ...fontDisplay }}>PITCHING</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: t.white, ...fontDisplay, marginTop: 2 }}>{a.pit.name}</div>
              <div style={{ ...fontMono, fontSize: 10, color: t.secondary, marginTop: 1 }}>{a.pit.era} ERA / {a.pit.pc} pc</div>
            </div>
          </div>
        )}

        {/* Condition Tags */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 10 }}>
          {a.wind && <Badge label={`${a.wind.dir} ${a.wind.mph} mph`} color="green" />}
          {a.temp && <Badge label={a.temp} color="amber" />}
          {a.pf && <Badge label={`PF ${a.pf}`} color="cyan" />}
          {a.pit?.velo && a.pit.velo !== "\u2014" && (
            <Badge label={`Velo ${a.pit.velo} mph`} color="red" />
          )}
        </div>

        {/* Expandable Factor Breakdown */}
        {a.factors && a.factors.length > 0 && (
          <>
            <div
              className="tap-target"
              onClick={onToggle}
              style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "10px 0", borderTop: `1px solid ${t.border}`,
              }}
            >
              <span style={{
                fontSize: 10, fontWeight: 700, color: t.muted,
                letterSpacing: "0.06em", ...fontDisplay,
              }}>WHY THIS CHIRP</span>
              <svg width="12" height="12" viewBox="0 0 12 12"
                style={{ transition: "transform 0.2s", transform: isExpanded ? "rotate(180deg)" : "" }}>
                <path d="M2 4.5L6 8.5L10 4.5" stroke={t.dim} strokeWidth="1.5" fill="none" strokeLinecap="round" />
              </svg>
            </div>

            {isExpanded && (
              <div className="fade-in" style={{ paddingBottom: 8 }}>
                {a.factors.map((f, i) => (
                  <div key={i} style={{ marginBottom: 12 }}>
                    <div style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      marginBottom: 4,
                    }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: t.primary, ...fontDisplay }}>{f.name}</span>
                      <span style={{ ...fontMono, fontSize: 11, fontWeight: 700, color: f.color }}>{f.mult}</span>
                    </div>
                    <div style={{
                      height: 3, background: "rgba(255,255,255,0.04)",
                      borderRadius: 2, overflow: "hidden", marginBottom: 3,
                    }}>
                      <div style={{
                        height: "100%", width: `${f.pct}%`, background: f.color,
                        borderRadius: 2, transition: "width 0.5s ease-out",
                      }} />
                    </div>
                    <span style={{ fontSize: 9, color: t.muted, ...fontDisplay, lineHeight: 1.3 }}>{f.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Action Bar — O/U Line */}
      <div
        className="tap-target"
        onClick={onTapLine}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 16px",
          background: t.greenBg,
          borderTop: `1px solid rgba(34,197,94,0.06)`,
        }}
      >
        <div>
          <span style={{ fontSize: 10, color: t.secondary, ...fontDisplay }}>{a.venue}</span>
          {level === "strong" && (
            <div style={{ fontSize: 9, color: t.muted, ...fontDisplay, marginTop: 1 }}>
              Tap for full breakdown
            </div>
          )}
        </div>
        <span style={{
          ...fontMono, fontSize: level === "strong" ? 22 : 18,
          fontWeight: 800, color: t.green, letterSpacing: "-0.03em",
        }}>{a.line}</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════
// SCOREBOARD STRIP
// ═══════════════════════════════════════

function ScoreboardStrip({ games }) {
  const levelColor = { strong: t.red, chirp: t.amber, soft: t.blue };
  return (
    <div
      className="hide-scroll"
      style={{
        display: "flex", gap: 8, overflowX: "auto",
        padding: "0 0 14px",
        borderBottom: `1px solid ${t.border}`,
        marginBottom: 4,
      }}
    >
      {games.map((g, i) => (
        <div key={i} style={{
          flexShrink: 0, minWidth: 110,
          background: t.card,
          border: `1px solid ${t.border}`,
          borderRadius: t.rs,
          borderLeft: g.chirp ? `2px solid ${levelColor[g.level]}` : `1px solid ${t.border}`,
          boxShadow: t.cardShadow,
          opacity: g.chirp ? 1 : 0.6,
        }}>
          <div style={{ padding: "8px 10px" }}>
            {[{ team: g.a, score: g.as }, { team: g.h, score: g.hs }].map((row, j) => (
              <div key={j} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                marginBottom: j === 0 ? 3 : 0,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <TeamLogo team={row.team} size={14} />
                  <span style={{ fontSize: 10, fontWeight: 700, color: t.primary, ...fontDisplay }}>
                    {TEAMS[row.team]?.abbr}
                  </span>
                </div>
                {g.inn && (
                  <span style={{ ...fontMono, fontSize: 11, fontWeight: 800, color: t.white }}>
                    {row.score}
                  </span>
                )}
              </div>
            ))}
            <div style={{
              marginTop: 5, display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <span style={{
                fontSize: 9, fontWeight: 600,
                color: g.inn ? t.green : t.muted, ...fontDisplay,
              }}>{g.inn || g.time}</span>
              {g.chirp && (
                <div style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: levelColor[g.level],
                  boxShadow: `0 0 4px ${levelColor[g.level]}40`,
                }} />
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════
// SCANNING SKELETON
// ═══════════════════════════════════════

function ScanningCard({ label }) {
  return (
    <div className="fade-in" style={{
      background: t.card,
      border: `1px solid ${t.border}`,
      borderRadius: t.r,
      boxShadow: t.cardShadow,
      padding: 16, marginBottom: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
        <div className="pulse-dot" style={{
          width: 6, height: 6, borderRadius: "50%", background: t.dim,
        }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: t.secondary, ...fontDisplay }}>
          {label}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <Skeleton w={24} h={24} r={12} />
        <Skeleton w={56} h={10} />
        <div style={{ flex: 1 }} />
        <Skeleton w={56} h={10} />
        <Skeleton w={24} h={24} r={12} />
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <Skeleton w={52} h={6} />
        <Skeleton w={64} h={6} />
        <Skeleton w={40} h={6} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════
// EMPTY STATE
// ═══════════════════════════════════════

function EmptyState() {
  return (
    <div style={{
      textAlign: "center", padding: "32px 24px 20px",
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: 14,
        background: "rgba(255,255,255,0.04)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginBottom: 12,
      }}>
        <span style={{ fontSize: 22 }}>&#x1F997;</span>
      </div>
      <div style={{ fontSize: 14, fontWeight: 600, color: t.secondary, ...fontDisplay }}>
        All quiet for now
      </div>
      <div style={{ fontSize: 11, color: t.muted, marginTop: 4, ...fontDisplay, lineHeight: 1.5 }}>
        Edges surface here when conditions align.
        <br />We're scanning every pitch.
      </div>
    </div>
  );
}

// ═══════════════════════════════════════
// BOTTOM SHEET
// ═══════════════════════════════════════

function BottomSheet({ open, onClose, title, children }) {
  const sheetRef = useRef(null);

  if (!open) return null;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100 }}>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "absolute", inset: 0,
          background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(6px)",
          WebkitBackdropFilter: "blur(6px)",
        }}
      />
      {/* Sheet */}
      <div
        ref={sheetRef}
        className="slide-up"
        style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          background: t.surface,
          borderRadius: "16px 16px 0 0",
          border: `1px solid ${t.borderHover}`,
          borderBottom: "none",
          maxHeight: "80vh",
          display: "flex", flexDirection: "column",
          boxShadow: "0 -8px 40px rgba(0,0,0,0.5)",
        }}
      >
        {/* Handle */}
        <div style={{ display: "flex", justifyContent: "center", padding: "10px 0 4px" }}>
          <div style={{ width: 32, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.12)" }} />
        </div>
        {/* Title bar */}
        {title && (
          <div style={{
            padding: "6px 20px 12px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: `1px solid ${t.border}`,
          }}>
            <span style={{ fontSize: 15, fontWeight: 700, color: t.white, ...fontDisplay }}>{title}</span>
            <div
              onClick={onClose}
              className="tap-target"
              style={{
                width: 28, height: 28, borderRadius: "50%",
                background: "rgba(255,255,255,0.06)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12">
                <path d="M2 2L10 10M10 2L2 10" stroke={t.muted} strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
          </div>
        )}
        {/* Content */}
        <div className="hide-scroll" style={{ flex: 1, overflowY: "auto", padding: "14px 20px 28px" }}>
          {children}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════
// BOTTOM NAV
// ═══════════════════════════════════════

function BottomNav({ activeCount }) {
  const items = [
    { icon: "\u26BE", label: "Games" },
    { icon: "\uD83E\uDD97", label: "Chirps", active: true, badge: activeCount },
    { icon: "\uD83D\uDCCA", label: "History" },
    { icon: null, label: "Settings", settingsIcon: true },
  ];

  return (
    <div style={{
      position: "sticky", bottom: 0, left: 0, right: 0,
      background: "rgba(6,8,12,0.92)",
      backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
      borderTop: `1px solid ${t.borderSubtle}`,
      padding: "8px 0 env(safe-area-inset-bottom, 16px)",
      display: "flex", justifyContent: "space-around",
    }}>
      {items.map((item) => (
        <div key={item.label} className="tap-target" style={{
          display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
          padding: "4px 16px", position: "relative", minWidth: 52,
          borderRadius: 8,
        }}>
          {item.settingsIcon ? (
            <svg width="18" height="18" viewBox="0 0 18 18" style={{ opacity: 0.35 }}>
              <circle cx="9" cy="9" r="3" stroke={t.white} strokeWidth="1.2" fill="none" />
              <circle cx="9" cy="2" r="1" fill={t.white} />
              <circle cx="9" cy="16" r="1" fill={t.white} />
              <circle cx="2" cy="9" r="1" fill={t.white} />
              <circle cx="16" cy="9" r="1" fill={t.white} />
            </svg>
          ) : (
            <span style={{ fontSize: 17, opacity: item.active ? 1 : 0.35 }}>{item.icon}</span>
          )}
          <span style={{
            fontSize: 9, fontWeight: item.active ? 700 : 500,
            color: item.active ? t.white : t.dim, ...fontDisplay,
          }}>{item.label}</span>
          {item.badge > 0 && (
            <div style={{
              position: "absolute", top: -1, right: 6,
              minWidth: 14, height: 14, borderRadius: 7,
              background: t.red,
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: "0 0 6px rgba(239,68,68,0.35)",
            }}>
              <span style={{ fontSize: 8, fontWeight: 800, color: "#fff" }}>{item.badge}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════
// MAIN CHIRPS SCREEN
// ═══════════════════════════════════════

export default function ChirpsScreen() {
  const [expandedId, setExpandedId] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetAlert, setSheetAlert] = useState(null);

  useEffect(() => { injectCSS(); }, []);

  // --- Mock Data ---
  const alerts = [
    {
      id: "c1", level: "strong", edge: 14.2,
      t1: "NYY", t2: "BOS", s1: 4, s2: 2, inn: 6, top: true, outs: 1,
      bases: [true, false, true],
      bat: { name: "A. Judge", avg: ".312", iso: ".290", hr: 22 },
      pit: { name: "C. Sale", era: "3.89", pc: 94, velo: "-2.1" },
      wind: { dir: "out", mph: 14 }, temp: "72\u00B0F",
      venue: "Fenway Park", pf: 104, line: "OVER 8.5", time: "2m ago",
      factors: [
        { name: "Judge elite power vs LHP", mult: "1.40x", pct: 85, color: t.blue, detail: "ISO .290 \u00B7 22 HR in 68 G \u00B7 vs LHP .341" },
        { name: "Pitcher fatigue detected", mult: "1.35x", pct: 78, color: t.red, detail: "94 pitches \u00B7 velo down 2.1 mph \u00B7 slider flat" },
        { name: "Wind blowing out to CF", mult: "1.25x", pct: 65, color: t.green, detail: "14 mph to CF \u00B7 Fenway Green Monster" },
        { name: "Hitter-friendly park factor", mult: "1.15x", pct: 55, color: t.amber, detail: "Fenway PF 104 \u00B7 HR factor 112" },
        { name: "High-leverage runner position", mult: "1.20x", pct: 70, color: t.cyan, detail: "RE24: 1st & 3rd, 1 out = 1.54 expected runs" },
      ],
    },
    {
      id: "c2", level: "chirp", edge: 8.7,
      t1: "LAD", t2: "SF", s1: 1, s2: 3, inn: 4, top: false, outs: 2,
      bases: [false, true, false],
      bat: { name: "M. Betts", avg: ".289", iso: ".245", hr: 18 },
      pit: { name: "L. Webb", era: "3.12", pc: 61, velo: "+0.3" },
      wind: { dir: "cross", mph: 8 }, temp: "64\u00B0F",
      venue: "Oracle Park", pf: 95, line: "UNDER 7.0", time: "8m ago",
      factors: [
        { name: "Betts vs sinkerball", mult: "1.20x", pct: 60, color: t.blue, detail: "ISO .245 \u00B7 pulls 43% \u00B7 sinker .189 BA" },
        { name: "Webb pitch efficiency", mult: "1.15x", pct: 55, color: t.red, detail: "61 pitches thru 4 \u00B7 slider 34% whiff" },
      ],
    },
    {
      id: "c3", level: "soft", edge: 5.1,
      t1: "ATL", t2: "PHI", s1: 0, s2: 0, inn: 0, top: true, outs: 0,
      bases: [false, false, false],
      bat: { name: "\u2014", avg: "\u2014", iso: "\u2014", hr: "\u2014" },
      pit: { name: "M. Fried", era: "2.65", pc: 0, velo: "\u2014" },
      wind: { dir: "out", mph: 11 }, temp: "78\u00B0F",
      venue: "Citizens Bank Park", pf: 108, line: "OVER 9.0", time: "Pre-game",
      factors: [
        { name: "Wind + park combo", mult: "1.18x", pct: 58, color: t.green, detail: "11 mph out \u00B7 CBP PF 108 \u00B7 HR factor 118" },
        { name: "Hot temperature", mult: "1.10x", pct: 45, color: t.amber, detail: "78\u00B0F \u00B7 ball carries +3% distance" },
      ],
    },
  ];

  const liveGames = [
    { a: "NYY", h: "BOS", as: 4, hs: 2, inn: "T6", chirp: true, level: "strong" },
    { a: "LAD", h: "SF", as: 1, hs: 3, inn: "B4", chirp: true, level: "chirp" },
    { a: "ATL", h: "PHI", as: 0, hs: 0, time: "7:10", chirp: true, level: "soft" },
    { a: "HOU", h: "TEX", as: 0, hs: 0, time: "7:05", chirp: false, level: null },
    { a: "CHC", h: "STL", as: 0, hs: 0, time: "7:15", chirp: false, level: null },
  ];

  const activeEdges = alerts.length;
  const liveCount = liveGames.filter((g) => g.inn).length;

  const openSheet = (alert) => {
    setSheetAlert(alert);
    setSheetOpen(true);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: t.bg,
      color: t.white,
      ...fontDisplay,
      display: "flex",
      flexDirection: "column",
    }}>
      {/* ── App Header ── */}
      <header style={{
        padding: "12px 20px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: `1px solid ${t.borderSubtle}`,
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(6,8,12,0.92)",
        backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "linear-gradient(135deg, #EF4444 0%, #F59E0B 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 8px rgba(239,68,68,0.15)",
          }}>
            <span style={{ fontSize: 14 }}>&#x1F997;</span>
          </div>
          <span style={{
            fontSize: 17, fontWeight: 800, color: t.white, letterSpacing: "-0.02em",
          }}>chirp</span>
          <span style={{
            fontSize: 9, fontWeight: 600, color: t.dim,
            background: "rgba(255,255,255,0.04)",
            padding: "2px 6px", borderRadius: 4,
          }}>BETA</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <div className="pulse-dot" style={{
            width: 5, height: 5, borderRadius: "50%", background: t.green,
            boxShadow: "0 0 4px rgba(34,197,94,0.4)",
          }} />
          <span style={{ fontSize: 10, fontWeight: 600, color: t.green }}>LIVE</span>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="hide-scroll" style={{
        flex: 1, overflowY: "auto", overflowX: "hidden",
        padding: "16px 16px 0",
        maxWidth: 520, width: "100%", margin: "0 auto",
      }}>

        {/* Page Title */}
        <div className="fade-in" style={{ marginBottom: 14 }}>
          <h1 style={{
            fontSize: 24, fontWeight: 800, margin: 0, letterSpacing: "-0.03em",
          }}>Chirps</h1>
          <p style={{
            fontSize: 12, color: t.muted, margin: "4px 0 0", lineHeight: 1.4,
          }}>
            {activeEdges} active edge{activeEdges !== 1 ? "s" : ""} &middot; {liveCount} live game{liveCount !== 1 ? "s" : ""}
          </p>
        </div>

        {/* Scoreboard Strip */}
        <ScoreboardStrip games={liveGames} />

        {/* Chirp Cards */}
        <div style={{ paddingTop: 8 }}>
          {alerts.map((alert) => (
            <ChirpCard
              key={alert.id}
              alert={alert}
              level={alert.level}
              expanded={expandedId === alert.id}
              onToggle={() => setExpandedId(expandedId === alert.id ? null : alert.id)}
              onTapLine={() => openSheet(alert)}
            />
          ))}
        </div>

        {/* Scanning State */}
        <ScanningCard label="Scanning CHC @ STL..." />

        {/* Empty State */}
        <EmptyState />

      </main>

      {/* ── Bottom Nav ── */}
      <BottomNav activeCount={activeEdges} />

      {/* ── Bottom Sheet ── */}
      <BottomSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title="Edge Breakdown"
      >
        {sheetAlert && (
          <div>
            {/* Sheet Header */}
            <div style={{
              display: "flex", alignItems: "center", gap: 10, marginBottom: 20,
            }}>
              <Badge
                label={sheetAlert.level === "strong" ? "STRONG CHIRP" : sheetAlert.level === "chirp" ? "CHIRP" : "SOFT CHIRP"}
                color={sheetAlert.level === "strong" ? "red" : sheetAlert.level === "chirp" ? "amber" : "blue"}
                pulse={sheetAlert.level === "strong"}
              />
              <span style={{
                ...fontMono, fontSize: 22, fontWeight: 800,
                color: sheetAlert.level === "strong" ? t.red : sheetAlert.level === "chirp" ? t.amber : t.blue,
              }}>
                +{sheetAlert.edge}%
              </span>
            </div>

            {/* Factors */}
            {sheetAlert.factors.map((f, i) => (
              <div key={i} style={{ marginBottom: 16 }}>
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  marginBottom: 5,
                }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: t.primary, ...fontDisplay }}>{f.name}</span>
                  <span style={{ ...fontMono, fontSize: 12, fontWeight: 700, color: f.color }}>{f.mult}</span>
                </div>
                <div style={{
                  height: 4, background: "rgba(255,255,255,0.04)",
                  borderRadius: 2, overflow: "hidden", marginBottom: 5,
                }}>
                  <div style={{
                    height: "100%", width: `${f.pct}%`, background: f.color,
                    borderRadius: 2, transition: "width 0.6s ease-out",
                  }} />
                </div>
                <span style={{ fontSize: 10, color: t.muted, ...fontDisplay, lineHeight: 1.4 }}>{f.detail}</span>
              </div>
            ))}

            {/* O/U Summary */}
            <div style={{
              marginTop: 12, padding: "16px 18px",
              background: t.greenBg,
              borderRadius: t.rs,
              border: "1px solid rgba(34,197,94,0.08)",
              textAlign: "center",
            }}>
              <span style={{ ...fontMono, fontSize: 20, fontWeight: 800, color: t.green }}>
                {sheetAlert.line}
              </span>
              <div style={{
                fontSize: 11, color: t.secondary, marginTop: 6, ...fontDisplay, lineHeight: 1.4,
              }}>
                Edge suggests this line is <strong style={{ color: t.green }}>+{sheetAlert.edge}%</strong> favorable
              </div>
            </div>
          </div>
        )}
      </BottomSheet>
    </div>
  );
}
