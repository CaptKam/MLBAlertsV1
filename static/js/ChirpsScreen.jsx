import React, { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// CHIRP.BET — CHIRPS SCREEN
// Redesigned per Apple HIG, Material Design 3, Nielsen Heuristics
// + patterns from old Chirpbot (GameCard, Diamond, Weather, Alerts)
//
// Design Rules Applied:
//   - 8pt grid spacing (4/8/12/16/24/32/48)
//   - 3-layer dark surface system (no pure black)
//   - White opacity text hierarchy (1.0/0.75/0.60/0.40/0.25)
//   - 44px minimum tap targets
//   - 4.5:1 WCAG contrast ratios
//   - Max 3 type sizes per screen section
//   - Skeleton loading (not spinners)
//   - Ease-out enter / ease-in exit animations
//   - One accent color per interactive role
//   - Bottom sheet with drag handle
//   - System status visibility on every state change
//   - Color never sole indicator of meaning
// ═══════════════════════════════════════════════════════════════

// --- ESPN Logo Helper ---
const ESPN_LOGO = (id) =>
  `https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/${id}.png&h=80&w=80`;

// --- Full 30-team MLB Data ---
const TEAMS = {
  NYY: { abbr: "NYY", name: "Yankees",   color: "#003087", espn: "nyy" },
  BOS: { abbr: "BOS", name: "Red Sox",   color: "#BD3039", espn: "bos" },
  LAD: { abbr: "LAD", name: "Dodgers",   color: "#005A9C", espn: "lad" },
  SF:  { abbr: "SF",  name: "Giants",    color: "#FD5A1E", espn: "sf"  },
  HOU: { abbr: "HOU", name: "Astros",    color: "#002D62", espn: "hou" },
  TEX: { abbr: "TEX", name: "Rangers",   color: "#003278", espn: "tex" },
  CHC: { abbr: "CHC", name: "Cubs",      color: "#0E3386", espn: "chc" },
  STL: { abbr: "STL", name: "Cardinals", color: "#C41E3A", espn: "stl" },
  ATL: { abbr: "ATL", name: "Braves",    color: "#CE1141", espn: "atl" },
  PHI: { abbr: "PHI", name: "Phillies",  color: "#E81828", espn: "phi" },
  NYM: { abbr: "NYM", name: "Mets",      color: "#002D72", espn: "nym" },
  MIL: { abbr: "MIL", name: "Brewers",   color: "#12284B", espn: "mil" },
  SD:  { abbr: "SD",  name: "Padres",    color: "#2F241D", espn: "sd"  },
  SEA: { abbr: "SEA", name: "Mariners",  color: "#0C2C56", espn: "sea" },
  TB:  { abbr: "TB",  name: "Rays",      color: "#092C5C", espn: "tb"  },
  MIN: { abbr: "MIN", name: "Twins",     color: "#002B5C", espn: "min" },
  CLE: { abbr: "CLE", name: "Guardians", color: "#00385D", espn: "cle" },
  DET: { abbr: "DET", name: "Tigers",    color: "#0C2340", espn: "det" },
  KC:  { abbr: "KC",  name: "Royals",    color: "#004687", espn: "kc"  },
  BAL: { abbr: "BAL", name: "Orioles",   color: "#DF4601", espn: "bal" },
  CWS: { abbr: "CWS", name: "White Sox", color: "#27251F", espn: "chw" },
  TOR: { abbr: "TOR", name: "Blue Jays", color: "#134A8E", espn: "tor" },
  LAA: { abbr: "LAA", name: "Angels",    color: "#BA0021", espn: "laa" },
  OAK: { abbr: "OAK", name: "Athletics", color: "#003831", espn: "oak" },
  PIT: { abbr: "PIT", name: "Pirates",   color: "#27251F", espn: "pit" },
  CIN: { abbr: "CIN", name: "Reds",      color: "#C6011F", espn: "cin" },
  COL: { abbr: "COL", name: "Rockies",   color: "#33006F", espn: "col" },
  ARI: { abbr: "ARI", name: "D-backs",   color: "#A71930", espn: "ari" },
  WSH: { abbr: "WSH", name: "Nationals", color: "#AB0003", espn: "wsh" },
  MIA: { abbr: "MIA", name: "Marlins",   color: "#00A3E0", espn: "mia" },
};

// ═══════════════════════════════════════
// DESIGN TOKENS
// Per dark theme rules: no pure black,
// 3-layer surface, white opacity text
// ═══════════════════════════════════════

const t = {
  // 3-Layer Surface System (Section 07)
  bg:       "#0D0D0D",   // Layer 1: Page canvas
  surface:  "#161B22",   // Layer 2: Cards, panels
  elevated: "#1E2530",   // Layer 3: Dropdowns, modals, sheets
  hover:    "#252D3A",   // Active/hover state

  // White Opacity Text System (Section 07)
  textPrimary:   "rgba(255,255,255,1.0)",    // Headlines, scores, prices
  textSecondary: "rgba(255,255,255,0.75)",   // Card titles, tab labels
  textBody:      "rgba(255,255,255,0.60)",   // Descriptions, supporting
  textCaption:   "rgba(255,255,255,0.40)",   // Timestamps, metadata
  textDisabled:  "rgba(255,255,255,0.25)",   // Disabled states
  textBorder:    "rgba(255,255,255,0.08)",   // Borders, dividers
  textHoverBg:   "rgba(255,255,255,0.05)",   // Hover backgrounds

  // Semantic Accent Colors (Section 05 — one per role)
  accent:    "#3B82F6",  // Primary interactive (buttons, active states)
  success:   "#22C55E",  // Success, live, confirmed
  danger:    "#EF4444",  // Errors, strong alerts, destructive
  warning:   "#F59E0B",  // Warnings, medium alerts
  info:      "#06B6D4",  // Info badges, park factor

  // Alert Level Colors (mapped to semantic)
  strong:    "#EF4444",  // = danger
  chirp:     "#F59E0B",  // = warning
  soft:      "#3B82F6",  // = accent

  // Spacing — 8pt grid (Section 05)
  sp4:  4,   sp8:  8,   sp12: 12,  sp16: 16,
  sp24: 24,  sp32: 32,  sp48: 48,

  // Border Radius
  r8:  8,   r12: 12,  r16: 16,

  // Shadows
  cardShadow:  "0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
  sheetShadow: "0 -8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06)",
  modalShadow: "0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06)",

  // Min tap target (Section 02 — Apple HIG 44pt)
  minTap: 44,
};

// Font stacks — weight bumped +1 for dark bg (Section 05)
const font = {
  display: "'Inter','SF Pro Display',-apple-system,system-ui,sans-serif",
  mono: "'JetBrains Mono','SF Mono','Menlo',monospace",
};

const ordinal = (n) => {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

// ═══════════════════════════════════════
// CSS INJECTION
// Animation rules per Section 06:
//   ease-out for enter, ease-in for exit
//   no linear on visible animations
//   shimmer for loading skeletons
// ═══════════════════════════════════════

const CSS_ID = "chirps-v3-css";
const injectCSS = () => {
  if (typeof document === "undefined" || document.getElementById(CSS_ID)) return;
  const el = document.createElement("style");
  el.id = CSS_ID;
  el.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    *, *::before, *::after { box-sizing: border-box; }

    /* Enter animation — ease-out decelerate (Section 06) */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.25s cubic-bezier(0.0, 0.0, 0.2, 1) both; }

    /* Pulse for live indicators */
    @keyframes pulseDot {
      0%, 100% { opacity: 1; }
      50%      { opacity: 0.3; }
    }
    .pulse-dot { animation: pulseDot 2s ease-in-out infinite; }

    /* Skeleton shimmer (Section 09 — skeleton over spinners) */
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
      animation: shimmer 1.5s ease infinite;
    }

    /* Sheet enter — ease-out (Section 06) */
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to   { transform: translateY(0); }
    }
    .slide-up { animation: slideUp 0.4s cubic-bezier(0.0, 0.0, 0.2, 1); }

    /* Modal enter — ease-out scale */
    @keyframes modalIn {
      from { opacity: 0; transform: scale(0.96) translateY(8px); }
      to   { opacity: 1; transform: scale(1) translateY(0); }
    }
    .modal-enter { animation: modalIn 0.25s cubic-bezier(0.0, 0.0, 0.2, 1); }

    /* Backdrop enter */
    @keyframes backdropIn {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    .backdrop-enter { animation: backdropIn 0.2s cubic-bezier(0.0, 0.0, 0.2, 1); }

    /* Hide scrollbar utility */
    .hide-scroll::-webkit-scrollbar { display: none; }
    .hide-scroll { scrollbar-width: none; }

    /* Custom scrollbar */
    .custom-scroll::-webkit-scrollbar { width: 4px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,0.08);
      border-radius: 2px;
    }

    /* Card hover — 150ms per Section 06 button feedback */
    .chirp-card {
      transition: transform 0.15s cubic-bezier(0.0, 0.0, 0.2, 1),
                  box-shadow 0.15s cubic-bezier(0.0, 0.0, 0.2, 1);
    }
    .chirp-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.08);
    }

    /* Tap target — 44px min, visible feedback <100ms (Section 06) */
    .tap-target {
      cursor: pointer;
      transition: background 0.1s cubic-bezier(0.0, 0.0, 0.2, 1);
      user-select: none;
      min-height: 44px;
      display: flex;
      align-items: center;
    }
    .tap-target:hover { background: rgba(255,255,255,0.04) !important; }
    .tap-target:active { background: rgba(255,255,255,0.06) !important; }

    /* Nav item */
    .nav-item {
      transition: background 0.1s cubic-bezier(0.0, 0.0, 0.2, 1);
      cursor: pointer;
      user-select: none;
      min-height: 44px;
    }
    .nav-item:hover { background: rgba(255,255,255,0.04); }

    /* Scoreboard chip */
    .scoreboard-chip {
      transition: transform 0.15s cubic-bezier(0.0, 0.0, 0.2, 1),
                  box-shadow 0.15s cubic-bezier(0.0, 0.0, 0.2, 1);
      cursor: pointer;
      min-height: 44px;
    }
    .scoreboard-chip:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }

    /* Filter button — 44px min tap */
    .filter-btn {
      transition: all 0.1s cubic-bezier(0.0, 0.0, 0.2, 1);
      cursor: pointer;
      user-select: none;
      min-height: 44px;
      display: flex;
      align-items: center;
    }
    .filter-btn:hover { background: rgba(255,255,255,0.06) !important; }

    /* Responsive grid for chirp cards */
    .chirps-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: 1fr;
    }
    @media (min-width: 900px) {
      .chirps-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (min-width: 1400px) {
      .chirps-grid { grid-template-columns: repeat(3, 1fr); }
    }

    /* Reduce Motion support (Section 06 — mandatory) */
    @media (prefers-reduced-motion: reduce) {
      .fade-in,
      .slide-up,
      .modal-enter,
      .backdrop-enter { animation: none !important; }
      .chirp-card,
      .tap-target,
      .nav-item,
      .scoreboard-chip,
      .filter-btn { transition: none !important; }
      .pulse-dot { animation: none !important; }
      .shimmer { animation: none !important; }
    }
  `;
  document.head.appendChild(el);
};


// ═══════════════════════════════════════
// PRIMITIVES
// ═══════════════════════════════════════

function TeamLogo({ team, size = 32 }) {
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
        alt={data.name}
        style={{ width: size * 0.78, height: size * 0.78, objectFit: "contain" }}
        onError={(e) => { e.target.style.display = "none"; }}
      />
    </div>
  );
}

// Baseball Diamond — pulled from old Chirpbot baseball-diamond.tsx
// Shows base runners + count (balls-strikes) + outs
function Diamond({ bases = [false, false, false], size = 44, balls = 0, strikes = 0, outs = 0, showCount = true }) {
  const m = size / 2;
  const d = size * 0.13;
  const pos = [
    { x: size * 0.85, y: m },       // 1st
    { x: m, y: size * 0.15 },       // 2nd
    { x: size * 0.15, y: m },       // 3rd
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: t.sp4 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <polygon
          points={`${m},${size * 0.15} ${size * 0.85},${m} ${m},${size * 0.85} ${size * 0.15},${m}`}
          fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="0.8"
        />
        {/* Home plate */}
        <rect
          x={m - d / 2} y={size * 0.85 - d / 2} width={d} height={d}
          fill={t.elevated} stroke="rgba(255,255,255,0.12)" strokeWidth="0.6"
          transform={`rotate(45 ${m} ${size * 0.85})`}
        />
        {/* Bases — color + icon indicator (not color alone per Section 05) */}
        {pos.map((p, i) => (
          <rect key={i}
            x={p.x - d / 2} y={p.y - d / 2} width={d} height={d}
            fill={bases[i] ? t.success : t.elevated}
            stroke={bases[i] ? "rgba(34,197,94,0.5)" : "rgba(255,255,255,0.10)"}
            strokeWidth={bases[i] ? "1" : "0.6"}
            transform={`rotate(45 ${p.x} ${p.y})`}
          />
        ))}
      </svg>
      {/* Count display — from old Chirpbot BaseballDiamond */}
      {showCount && (
        <div style={{ display: "flex", alignItems: "center", gap: t.sp8, fontFamily: font.mono }}>
          {(balls > 0 || strikes > 0) && (
            <span style={{ fontSize: 10, fontWeight: 600, color: t.success }}>
              {balls}-{strikes}
            </span>
          )}
          <OutDots count={outs} />
        </div>
      )}
    </div>
  );
}

function OutDots({ count = 0 }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 3 }}>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: "50%",
          background: i < count ? t.warning : "rgba(255,255,255,0.08)",
          boxShadow: i < count ? "0 0 4px rgba(245,158,11,0.3)" : "none",
        }} />
      ))}
      {/* Text label so color is not sole indicator */}
      <span style={{
        fontSize: 9, fontWeight: 600, color: t.textCaption,
        fontFamily: font.display, marginLeft: 2,
      }}>
        {count} out{count !== 1 ? "s" : ""}
      </span>
    </div>
  );
}

// Weather Display — pulled from old Chirpbot WeatherDisplay component
function WeatherDisplay({ windSpeed, windDirection, windGust, temperature, size = "sm" }) {
  const windIcons = {
    N: "\u2191", S: "\u2193", E: "\u2192", W: "\u2190",
    NE: "\u2197", NW: "\u2196", SE: "\u2198", SW: "\u2199",
    out: "\u2197", cross: "\u2194", in: "\u2199",
  };
  const arrow = windIcons[windDirection] || "\u2191";
  const fs = size === "sm" ? 10 : 12;

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.sp4,
      fontSize: fs, fontFamily: font.mono,
    }}>
      <span style={{ color: t.textCaption }}>{arrow}</span>
      <span style={{ color: t.textBody, fontWeight: 500 }}>
        {windSpeed}mph {windDirection}
        {windGust && windGust > windSpeed + 3 && (
          <span style={{ color: t.warning, marginLeft: 4 }}>
            (gusts {windGust})
          </span>
        )}
      </span>
      {temperature && (
        <>
          <span style={{ color: t.textDisabled }}>&middot;</span>
          <span style={{ color: t.textBody }}>{temperature}</span>
        </>
      )}
    </div>
  );
}

// Badge — with icon+text (color never sole indicator)
function Badge({ label, color = "success", pulse = false, icon }) {
  const colors = {
    danger: t.danger, success: t.success, accent: t.accent,
    warning: t.warning, info: t.info,
    red: t.danger, green: t.success, blue: t.accent,
    amber: t.warning, cyan: t.info,
  };
  const c = colors[color] || color;
  return (
    <span className={pulse ? "pulse-dot" : ""} style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: `${t.sp4}px ${t.sp8}px`, borderRadius: 6,
      background: `${c}12`, border: `1px solid ${c}20`,
      fontSize: 10, fontWeight: 600, color: c,
      letterSpacing: "0.02em", fontFamily: font.display,
      whiteSpace: "nowrap",
    }}>
      {icon && <span style={{ fontSize: 10 }}>{icon}</span>}
      {label}
    </span>
  );
}

// Confidence Badge — from old Chirpbot UniversalAlertCard
function ConfidenceBadge({ confidence, size = "sm" }) {
  let color = t.success;
  let label = "HIGH";
  if (confidence < 50) { color = t.textCaption; label = "LOW"; }
  else if (confidence < 70) { color = t.warning; label = "MED"; }

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.sp4,
      padding: `${t.sp4}px ${t.sp8}px`,
      background: `${color}10`, borderRadius: 6,
      border: `1px solid ${color}20`,
    }}>
      {/* Progress bar so not color-only */}
      <div style={{
        width: 24, height: 3, background: "rgba(255,255,255,0.06)",
        borderRadius: 2, overflow: "hidden",
      }}>
        <div style={{
          width: `${confidence}%`, height: "100%",
          background: color, borderRadius: 2,
        }} />
      </div>
      <span style={{
        fontSize: size === "sm" ? 9 : 10, fontWeight: 700,
        color, fontFamily: font.mono,
      }}>
        {confidence}%
      </span>
    </div>
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

// Stat box for desktop summary row
function StatBox({ label, value, color = t.textPrimary, sub }) {
  return (
    <div style={{
      padding: t.sp16,
      background: t.surface,
      border: `1px solid ${t.textBorder}`,
      borderRadius: t.r12,
    }}>
      <div style={{
        fontSize: 10, fontWeight: 600, color: t.textCaption,
        letterSpacing: "0.04em", fontFamily: font.display, marginBottom: t.sp8,
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: font.mono, fontSize: 24, fontWeight: 800,
        color, letterSpacing: "-0.03em",
      }}>
        {value}
      </div>
      {sub && (
        <div style={{
          fontSize: 10, color: t.textCaption, fontFamily: font.display, marginTop: t.sp4,
        }}>{sub}</div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════
// NAVIGATION — Sidebar (desktop) + Bottom Tab Bar (mobile)
// Per Section 04: tab bar 3-5 tabs, always visible,
// icon + label, pinned to bottom safe area
// ═══════════════════════════════════════

function Sidebar({ activeTab, onTabChange, alertCount }) {
  const navItems = [
    { id: "games",    label: "Games",    icon: "\u26BE" },
    { id: "chirps",   label: "Chirps",   icon: "\u26A1", badge: alertCount },
    { id: "history",  label: "History",  icon: "\uD83D\uDCCA" },
    { id: "settings", label: "Settings", icon: "\u2699\uFE0F" },
  ];

  return (
    <aside style={{
      width: 220, height: "100vh", position: "fixed",
      left: 0, top: 0, background: t.surface,
      borderRight: `1px solid ${t.textBorder}`,
      display: "flex", flexDirection: "column", zIndex: 40,
    }}>
      {/* Logo */}
      <div style={{ padding: `${t.sp24}px ${t.sp24}px ${t.sp16}px`, borderBottom: `1px solid ${t.textBorder}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.sp12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: t.r12,
            background: "linear-gradient(135deg, #EF4444 0%, #F59E0B 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 8px rgba(239,68,68,0.2)",
          }}>
            <span style={{ fontSize: 18 }}>&#x1F997;</span>
          </div>
          <div>
            <span style={{
              fontSize: 18, fontWeight: 800, color: t.textPrimary,
              fontFamily: font.display, display: "block", lineHeight: 1,
            }}>chirp</span>
            <span style={{
              fontSize: 9, fontWeight: 600, color: t.textDisabled,
              fontFamily: font.display, letterSpacing: "0.06em",
            }}>BETA</span>
          </div>
        </div>
      </div>

      {/* Nav — each item is 44px min tap target */}
      <nav style={{ flex: 1, padding: `${t.sp12}px ${t.sp8}px`, overflow: "hidden" }}>
        {navItems.map((item) => {
          const active = activeTab === item.id;
          return (
            <div
              key={item.id}
              className="nav-item"
              onClick={() => onTabChange(item.id)}
              role="button"
              tabIndex={0}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              onKeyDown={(e) => { if (e.key === "Enter") onTabChange(item.id); }}
              style={{
                display: "flex", alignItems: "center", gap: t.sp12,
                padding: `${t.sp12}px ${t.sp12}px`,
                borderRadius: t.r8, marginBottom: 2,
                background: active ? "rgba(255,255,255,0.06)" : "transparent",
                position: "relative", minHeight: t.minTap,
              }}
            >
              <span style={{ fontSize: 16, opacity: active ? 1 : 0.5 }}>{item.icon}</span>
              <span style={{
                fontSize: 13, fontWeight: active ? 600 : 500,
                color: active ? t.textPrimary : t.textBody,
                fontFamily: font.display, flex: 1,
              }}>{item.label}</span>
              {item.badge > 0 && (
                <div style={{
                  minWidth: 20, height: 20, borderRadius: 10,
                  background: t.danger, display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 0 6px rgba(239,68,68,0.3)",
                }}>
                  <span style={{ fontSize: 9, fontWeight: 800, color: "#fff" }}>{item.badge}</span>
                </div>
              )}
              {active && (
                <div style={{
                  position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)",
                  width: 3, height: 20, borderRadius: 2, background: t.accent,
                }} />
              )}
            </div>
          );
        })}
      </nav>

      {/* Live status indicator — system status visibility (Heuristic 1) */}
      <div style={{ padding: `${t.sp16}px ${t.sp24}px`, borderTop: `1px solid ${t.textBorder}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.sp8 }}>
          <div className="pulse-dot" style={{
            width: 6, height: 6, borderRadius: "50%", background: t.success,
            boxShadow: "0 0 6px rgba(34,197,94,0.4)",
          }} />
          <span style={{ fontSize: 11, fontWeight: 600, color: t.success, fontFamily: font.display }}>
            LIVE
          </span>
          <span style={{
            fontSize: 10, color: t.textCaption, fontFamily: font.display, marginLeft: "auto",
          }}>
            Scanning
          </span>
        </div>
      </div>
    </aside>
  );
}

// Mobile Bottom Tab Bar — per Section 04: 3-5 tabs, always visible, icon + label
function MobileBottomNav({ activeTab, onTabChange, alertCount }) {
  const items = [
    { id: "games",    icon: "\u26BE",       label: "Games" },
    { id: "chirps",   icon: "\u26A1",       label: "Chirps", badge: alertCount },
    { id: "history",  icon: "\uD83D\uDCCA", label: "History" },
    { id: "settings", icon: "\u2699\uFE0F", label: "Settings" },
  ];

  return (
    <nav
      role="tablist"
      aria-label="Main navigation"
      style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        background: "rgba(13,13,13,0.95)",
        backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
        borderTop: `1px solid ${t.textBorder}`,
        padding: `${t.sp8}px 0 env(safe-area-inset-bottom, ${t.sp12}px)`,
        display: "flex", justifyContent: "space-around",
        zIndex: 50,
      }}
    >
      {items.map((item) => {
        const active = activeTab === item.id;
        return (
          <div
            key={item.id}
            role="tab"
            tabIndex={0}
            aria-selected={active}
            aria-label={item.label}
            onClick={() => onTabChange(item.id)}
            onKeyDown={(e) => { if (e.key === "Enter") onTabChange(item.id); }}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
              padding: `${t.sp8}px ${t.sp16}px`, position: "relative",
              minWidth: 52, minHeight: t.minTap,
              borderRadius: t.r8, cursor: "pointer",
            }}
          >
            <span style={{ fontSize: 18, opacity: active ? 1 : 0.35 }}>{item.icon}</span>
            <span style={{
              fontSize: 9, fontWeight: active ? 700 : 500,
              color: active ? t.textPrimary : t.textDisabled,
              fontFamily: font.display,
            }}>{item.label}</span>
            {item.badge > 0 && (
              <div style={{
                position: "absolute", top: 2, right: 6,
                minWidth: 16, height: 16, borderRadius: 8,
                background: t.danger,
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 0 6px rgba(239,68,68,0.35)",
              }}>
                <span style={{ fontSize: 8, fontWeight: 800, color: "#fff" }}>{item.badge}</span>
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}

// Mobile Header
function MobileHeader({ alertCount }) {
  return (
    <header style={{
      padding: `${t.sp12}px ${t.sp16}px`,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      borderBottom: `1px solid ${t.textBorder}`,
      background: "rgba(13,13,13,0.95)",
      backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
      position: "sticky", top: 0, zIndex: 50,
      minHeight: t.minTap,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.sp8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: t.r8,
          background: "linear-gradient(135deg, #EF4444 0%, #F59E0B 100%)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: 14 }}>&#x1F997;</span>
        </div>
        <span style={{ fontSize: 17, fontWeight: 800, color: t.textPrimary, fontFamily: font.display }}>chirp</span>
        <span style={{
          fontSize: 9, fontWeight: 600, color: t.textDisabled,
          background: "rgba(255,255,255,0.04)", padding: "2px 6px", borderRadius: 4,
        }}>BETA</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: t.sp8 }}>
        {alertCount > 0 && (
          <div style={{
            minWidth: 20, height: 20, borderRadius: 10,
            background: t.danger, display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ fontSize: 10, fontWeight: 800, color: "#fff" }}>{alertCount}</span>
          </div>
        )}
        <div className="pulse-dot" style={{
          width: 6, height: 6, borderRadius: "50%", background: t.success,
          boxShadow: "0 0 4px rgba(34,197,94,0.4)",
        }} />
        <span style={{ fontSize: 10, fontWeight: 600, color: t.success, fontFamily: font.display }}>LIVE</span>
      </div>
    </header>
  );
}


// ═══════════════════════════════════════
// SCOREBOARD STRIP
// ═══════════════════════════════════════

function ScoreboardStrip({ games }) {
  const levelColor = { strong: t.strong, chirp: t.chirp, soft: t.soft };
  return (
    <div
      className="hide-scroll"
      role="list"
      aria-label="Live games"
      style={{
        display: "flex", gap: t.sp12, overflowX: "auto",
        padding: `0 0 ${t.sp16}px`,
        borderBottom: `1px solid ${t.textBorder}`,
        marginBottom: t.sp8,
      }}
    >
      {games.map((g, i) => (
        <div key={i} className="scoreboard-chip" role="listitem" style={{
          flexShrink: 0, minWidth: 136,
          background: t.surface,
          border: `1px solid ${g.chirp ? `${levelColor[g.level]}30` : t.textBorder}`,
          borderRadius: t.r12,
          borderLeft: g.chirp ? `3px solid ${levelColor[g.level]}` : `1px solid ${t.textBorder}`,
          boxShadow: t.cardShadow,
          opacity: g.chirp ? 1 : 0.55,
        }}>
          <div style={{ padding: `${t.sp12}px ${t.sp12}px` }}>
            {[{ team: g.a, score: g.as }, { team: g.h, score: g.hs }].map((row, j) => (
              <div key={j} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                marginBottom: j === 0 ? t.sp4 : 0,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: t.sp4 }}>
                  <TeamLogo team={row.team} size={16} />
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: t.textSecondary, fontFamily: font.display,
                  }}>
                    {TEAMS[row.team]?.abbr}
                  </span>
                </div>
                {g.inn && (
                  <span style={{ fontFamily: font.mono, fontSize: 12, fontWeight: 800, color: t.textPrimary }}>
                    {row.score}
                  </span>
                )}
              </div>
            ))}
            <div style={{
              marginTop: t.sp8, display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <span style={{
                fontSize: 9, fontWeight: 600,
                color: g.inn ? t.success : t.textCaption, fontFamily: font.display,
              }}>
                {g.inn ? `${g.inn} \u2022 LIVE` : g.time}
              </span>
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
// CHIRP CARD
// Layout from old Chirpbot GameCardTemplate:
//   Away team | Center diamond | Home team
// + Edge breakdown, matchup context, weather
// ═══════════════════════════════════════

function ChirpCard({ alert, level, expanded, onToggle, onTapLine }) {
  const levelConfig = {
    strong: { color: t.strong, label: "STRONG CHIRP", icon: "\uD83D\uDD34" },
    chirp:  { color: t.chirp,  label: "CHIRP",        icon: "\uD83D\uDFE1" },
    soft:   { color: t.soft,   label: "SOFT CHIRP",   icon: "\uD83D\uDD35" },
  };
  const cfg = levelConfig[level];
  const a = alert;
  const isLive = a.inn > 0;

  return (
    <article
      className="chirp-card fade-in"
      role="article"
      aria-label={`${cfg.label}: ${TEAMS[a.t1]?.name || a.t1} at ${TEAMS[a.t2]?.name || a.t2}, edge ${a.edge}%`}
      style={{
        background: t.surface,
        border: `1px solid ${t.textBorder}`,
        borderRadius: t.r16,
        borderLeft: `3px solid ${cfg.color}`,
        boxShadow: level === "strong"
          ? `0 2px 20px rgba(0,0,0,0.35), 0 0 0 1px ${cfg.color}10`
          : t.cardShadow,
        overflow: "hidden",
      }}
    >
      <div style={{ padding: `${t.sp16}px ${t.sp16}px 0` }}>

        {/* Header: Level badge + Edge % + Time */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: t.sp16,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: t.sp12 }}>
            <Badge
              label={cfg.label}
              icon={cfg.icon}
              color={level === "strong" ? "danger" : level === "chirp" ? "warning" : "accent"}
              pulse={level === "strong"}
            />
            <span style={{
              fontFamily: font.mono,
              fontSize: level === "strong" ? 28 : 22,
              fontWeight: 800, color: cfg.color, letterSpacing: "-0.03em",
            }}>
              +{a.edge}%
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: t.sp8 }}>
            {a.confidence && <ConfidenceBadge confidence={a.confidence} />}
            <span style={{ fontSize: 10, color: t.textCaption, fontFamily: font.display }}>{a.time}</span>
          </div>
        </div>

        {/* Scoreboard — GameCardTemplate pattern: Away | Diamond | Home */}
        <div style={{
          padding: `${t.sp16}px`,
          background: "rgba(255,255,255,0.02)",
          borderRadius: t.r12,
          border: `1px solid ${t.textBorder}`,
          marginBottom: t.sp16,
        }}>
          <div style={{ display: "flex", alignItems: "center" }}>
            {/* Away Team */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: t.sp12 }}>
              <TeamLogo team={a.t1} size={isLive ? 36 : 28} />
              <div>
                <span style={{
                  fontSize: 14, fontWeight: 700, color: t.textPrimary,
                  fontFamily: font.display, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t1]?.abbr}</span>
                <span style={{ fontSize: 10, color: t.textCaption, fontFamily: font.display }}>
                  {TEAMS[a.t1]?.name}
                </span>
              </div>
              {isLive && (
                <span style={{
                  fontFamily: font.mono, fontSize: 28, fontWeight: 800,
                  color: t.textPrimary, marginLeft: "auto", letterSpacing: "-0.03em",
                }}>{a.s1}</span>
              )}
            </div>

            {/* Center — Diamond with count (from old Chirpbot) */}
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: t.sp4, margin: `0 ${t.sp16}px`, flexShrink: 0,
            }}>
              {isLive ? (
                <>
                  <Diamond
                    bases={a.bases}
                    size={44}
                    balls={a.balls || 0}
                    strikes={a.strikes || 0}
                    outs={a.outs}
                    showCount={true}
                  />
                  <div style={{ display: "flex", alignItems: "center", gap: t.sp4 }}>
                    <div className="pulse-dot" style={{
                      width: 5, height: 5, borderRadius: "50%", background: t.success,
                    }} />
                    <span style={{
                      fontSize: 10, fontWeight: 700, color: t.success, fontFamily: font.display,
                    }}>{a.top ? "\u25B2" : "\u25BC"}{ordinal(a.inn)}</span>
                  </div>
                </>
              ) : (
                <span style={{
                  fontSize: 12, fontWeight: 600, color: t.textCaption, fontFamily: font.display,
                }}>@ 7:10 PM</span>
              )}
            </div>

            {/* Home Team */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: t.sp12, flexDirection: "row-reverse" }}>
              <TeamLogo team={a.t2} size={isLive ? 36 : 28} />
              <div style={{ textAlign: "right" }}>
                <span style={{
                  fontSize: 14, fontWeight: 700, color: t.textPrimary,
                  fontFamily: font.display, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t2]?.abbr}</span>
                <span style={{ fontSize: 10, color: t.textCaption, fontFamily: font.display }}>
                  {TEAMS[a.t2]?.name}
                </span>
              </div>
              {isLive && (
                <span style={{
                  fontFamily: font.mono, fontSize: 28, fontWeight: 800,
                  color: t.textPrimary, marginRight: "auto", letterSpacing: "-0.03em",
                }}>{a.s2}</span>
              )}
            </div>
          </div>
        </div>

        {/* Matchup Context — batter vs pitcher */}
        {isLive && level !== "soft" && (
          <div style={{ display: "flex", gap: t.sp12, marginBottom: t.sp16 }}>
            <div style={{
              flex: 1, padding: `${t.sp12}px`, borderRadius: t.r8,
              background: `${t.accent}08`, border: `1px solid ${t.accent}12`,
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.accent, letterSpacing: "0.04em", fontFamily: font.display }}>AT BAT</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.textPrimary, fontFamily: font.display, marginTop: t.sp4 }}>{a.bat.name}</div>
              <div style={{ fontFamily: font.mono, fontSize: 10, color: t.textBody, marginTop: 2 }}>{a.bat.avg} / {a.bat.hr} HR</div>
            </div>
            <div style={{
              flex: 1, padding: `${t.sp12}px`, borderRadius: t.r8,
              background: `${t.danger}08`, border: `1px solid ${t.danger}12`,
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.danger, letterSpacing: "0.04em", fontFamily: font.display }}>PITCHING</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.textPrimary, fontFamily: font.display, marginTop: t.sp4 }}>{a.pit.name}</div>
              <div style={{ fontFamily: font.mono, fontSize: 10, color: t.textBody, marginTop: 2 }}>{a.pit.era} ERA / {a.pit.pc} pc</div>
            </div>
          </div>
        )}

        {/* Condition Tags — weather from old Chirpbot */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: t.sp4, marginBottom: t.sp12 }}>
          {a.wind && (
            <WeatherDisplay
              windSpeed={a.wind.mph}
              windDirection={a.wind.dir}
              temperature={a.temp}
            />
          )}
          {a.pf && <Badge label={`PF ${a.pf}`} icon="\uD83C\uDFDF\uFE0F" color="info" />}
          {a.pit?.velo && a.pit.velo !== "\u2014" && (
            <Badge label={`Velo ${a.pit.velo}`} icon="\uD83D\uDCA8" color="danger" />
          )}
        </div>

        {/* Expandable Factor Breakdown — 44px tap target */}
        {a.factors && a.factors.length > 0 && (
          <>
            <div
              className="tap-target"
              onClick={onToggle}
              role="button"
              tabIndex={0}
              aria-expanded={expanded}
              aria-label="Toggle edge breakdown"
              onKeyDown={(e) => { if (e.key === "Enter") onToggle(); }}
              style={{
                justifyContent: "space-between",
                padding: `0 0`, borderTop: `1px solid ${t.textBorder}`,
                borderRadius: 0,
              }}
            >
              <span style={{
                fontSize: 10, fontWeight: 700, color: t.textCaption,
                letterSpacing: "0.06em", fontFamily: font.display,
              }}>WHY THIS CHIRP</span>
              <svg width="12" height="12" viewBox="0 0 12 12"
                style={{ transition: "transform 0.2s cubic-bezier(0,0,0.2,1)", transform: expanded ? "rotate(180deg)" : "" }}>
                <path d="M2 4.5L6 8.5L10 4.5" stroke={t.textCaption} strokeWidth="1.5" fill="none" strokeLinecap="round" />
              </svg>
            </div>

            {expanded && (
              <div className="fade-in" style={{ paddingBottom: t.sp12 }}>
                {a.factors.map((f, i) => (
                  <div key={i} style={{ marginBottom: t.sp16 }}>
                    <div style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      marginBottom: t.sp4,
                    }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: t.textSecondary, fontFamily: font.display }}>{f.name}</span>
                      <span style={{ fontFamily: font.mono, fontSize: 12, fontWeight: 700, color: f.color }}>{f.mult}</span>
                    </div>
                    <div style={{
                      height: 4, background: "rgba(255,255,255,0.04)",
                      borderRadius: 2, overflow: "hidden", marginBottom: t.sp4,
                    }}>
                      <div style={{
                        height: "100%", width: `${f.pct}%`, background: f.color,
                        borderRadius: 2, transition: "width 0.5s cubic-bezier(0,0,0.2,1)",
                      }} />
                    </div>
                    <span style={{ fontSize: 10, color: t.textCaption, fontFamily: font.display, lineHeight: 1.5 }}>{f.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Action Bar — O/U line, 44px tap target */}
      <div
        className="tap-target"
        onClick={onTapLine}
        role="button"
        tabIndex={0}
        aria-label={`View full breakdown: ${a.line}`}
        onKeyDown={(e) => { if (e.key === "Enter") onTapLine(); }}
        style={{
          justifyContent: "space-between",
          padding: `0 ${t.sp16}px`,
          background: `${t.success}06`,
          borderTop: `1px solid ${t.success}08`,
          borderRadius: 0,
        }}
      >
        <div>
          <span style={{ fontSize: 11, color: t.textBody, fontFamily: font.display }}>{a.venue}</span>
          <div style={{ fontSize: 9, color: t.textCaption, fontFamily: font.display, marginTop: 2 }}>
            Click for full breakdown
          </div>
        </div>
        <span style={{
          fontFamily: font.mono, fontSize: level === "strong" ? 22 : 18,
          fontWeight: 800, color: t.success, letterSpacing: "-0.03em",
        }}>{a.line}</span>
      </div>
    </article>
  );
}


// ═══════════════════════════════════════
// SKELETON / EMPTY / ERROR STATES
// Per Section 09: skeleton screens over spinners
// Per Heuristic 9: error messages in plain English
// ═══════════════════════════════════════

function ScanningCard({ label }) {
  return (
    <div className="fade-in" role="status" aria-label="Scanning for edges" style={{
      background: t.surface,
      border: `1px solid ${t.textBorder}`,
      borderRadius: t.r16,
      boxShadow: t.cardShadow,
      padding: t.sp16,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.sp8, marginBottom: t.sp16 }}>
        <div className="pulse-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: t.textCaption }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: t.textBody, fontFamily: font.display }}>{label}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: t.sp12, marginBottom: t.sp12 }}>
        <Skeleton w={32} h={32} r={16} />
        <Skeleton w={64} h={12} />
        <div style={{ flex: 1 }} />
        <Skeleton w={64} h={12} />
        <Skeleton w={32} h={32} r={16} />
      </div>
      <div style={{ display: "flex", gap: t.sp8 }}>
        <Skeleton w={56} h={8} />
        <Skeleton w={72} h={8} />
        <Skeleton w={48} h={8} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div role="status" style={{
      textAlign: "center", padding: `${t.sp48}px ${t.sp24}px ${t.sp32}px`,
      gridColumn: "1 / -1",
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: t.r16,
        background: "rgba(255,255,255,0.04)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginBottom: t.sp16,
      }}>
        <span style={{ fontSize: 28 }}>&#x1F997;</span>
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: t.textSecondary, fontFamily: font.display }}>
        All quiet for now
      </div>
      <div style={{
        fontSize: 12, color: t.textCaption, marginTop: t.sp8,
        fontFamily: font.display, lineHeight: 1.6,
        maxWidth: 320, margin: `${t.sp8}px auto 0`,
      }}>
        Edges surface here when conditions align. We're scanning every pitch across all live games.
      </div>
    </div>
  );
}

// Error State — Heuristic 9: plain English, clear fix instructions
function ErrorState({ message, onRetry }) {
  return (
    <div role="alert" style={{
      textAlign: "center", padding: `${t.sp48}px ${t.sp24}px`,
      gridColumn: "1 / -1",
      background: `${t.danger}06`,
      borderRadius: t.r16,
      border: `1px solid ${t.danger}20`,
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: t.r16,
        background: `${t.danger}15`,
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginBottom: t.sp16,
      }}>
        <span style={{ fontSize: 24 }}>&#x26A0;&#xFE0F;</span>
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: t.textPrimary, fontFamily: font.display }}>
        {message || "Unable to load alerts"}
      </div>
      <div style={{
        fontSize: 12, color: t.textBody, marginTop: t.sp8,
        fontFamily: font.display, lineHeight: 1.6,
      }}>
        Check your connection and try again.
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: t.sp16, padding: `${t.sp12}px ${t.sp24}px`,
            background: `${t.danger}15`, border: `1px solid ${t.danger}30`,
            borderRadius: t.r8, color: t.danger,
            fontSize: 12, fontWeight: 600, fontFamily: font.display,
            cursor: "pointer", minHeight: t.minTap,
          }}
        >
          Retry Connection
        </button>
      )}
    </div>
  );
}


// ═══════════════════════════════════════
// MODAL (desktop) + BOTTOM SHEET (mobile)
// Per Section 04: bottom sheet for mobile
//   with drag handle, swipe dismiss
// Modal for desktop with ESC to close
// ═══════════════════════════════════════

function EdgeBreakdownPanel({ open, onClose, alert: a, isMobile }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handleEsc = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [open, onClose]);

  if (!open || !a) return null;

  const levelColor = a.level === "strong" ? t.strong : a.level === "chirp" ? t.chirp : t.soft;
  const levelLabel = a.level === "strong" ? "STRONG CHIRP" : a.level === "chirp" ? "CHIRP" : "SOFT CHIRP";
  const levelIcon = a.level === "strong" ? "\uD83D\uDD34" : a.level === "chirp" ? "\uD83D\uDFE1" : "\uD83D\uDD35";

  const content = (
    <div>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: t.sp12, marginBottom: t.sp24 }}>
        <Badge label={levelLabel} icon={levelIcon}
          color={a.level === "strong" ? "danger" : a.level === "chirp" ? "warning" : "accent"}
          pulse={a.level === "strong"} />
        <span style={{
          fontFamily: font.mono, fontSize: 26, fontWeight: 800,
          color: levelColor,
        }}>+{a.edge}%</span>
        {a.confidence && <ConfidenceBadge confidence={a.confidence} />}
      </div>

      {/* Matchup summary */}
      <div style={{
        display: "flex", alignItems: "center", gap: t.sp12, marginBottom: t.sp24,
        padding: t.sp16, background: "rgba(255,255,255,0.02)",
        borderRadius: t.r12, border: `1px solid ${t.textBorder}`,
      }}>
        <TeamLogo team={a.t1} size={28} />
        <span style={{ fontSize: 14, fontWeight: 700, color: t.textPrimary, fontFamily: font.display }}>{TEAMS[a.t1]?.abbr}</span>
        {a.inn > 0 && <span style={{ fontFamily: font.mono, fontSize: 18, fontWeight: 800, color: t.textPrimary }}>{a.s1}</span>}
        <span style={{ fontSize: 12, color: t.textDisabled, margin: `0 ${t.sp4}px` }}>vs</span>
        {a.inn > 0 && <span style={{ fontFamily: font.mono, fontSize: 18, fontWeight: 800, color: t.textPrimary }}>{a.s2}</span>}
        <span style={{ fontSize: 14, fontWeight: 700, color: t.textPrimary, fontFamily: font.display }}>{TEAMS[a.t2]?.abbr}</span>
        <TeamLogo team={a.t2} size={28} />
        <span style={{ marginLeft: "auto", fontSize: 11, color: t.textCaption, fontFamily: font.display }}>{a.venue}</span>
      </div>

      {/* Factors */}
      <div style={{ marginBottom: t.sp24 }}>
        <div style={{
          fontSize: 10, fontWeight: 700, color: t.textCaption, letterSpacing: "0.06em",
          fontFamily: font.display, marginBottom: t.sp16,
        }}>CONTRIBUTING FACTORS</div>
        {a.factors.map((f, i) => (
          <div key={i} style={{ marginBottom: t.sp16 }}>
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              marginBottom: t.sp8,
            }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: t.textSecondary, fontFamily: font.display }}>{f.name}</span>
              <span style={{ fontFamily: font.mono, fontSize: 13, fontWeight: 700, color: f.color }}>{f.mult}</span>
            </div>
            <div style={{
              height: 4, background: "rgba(255,255,255,0.04)",
              borderRadius: 2, overflow: "hidden", marginBottom: t.sp8,
            }}>
              <div style={{
                height: "100%", width: `${f.pct}%`, background: f.color,
                borderRadius: 2, transition: "width 0.6s cubic-bezier(0,0,0.2,1)",
              }} />
            </div>
            <span style={{ fontSize: 11, color: t.textCaption, fontFamily: font.display, lineHeight: 1.5 }}>{f.detail}</span>
          </div>
        ))}
      </div>

      {/* O/U Summary */}
      <div style={{
        padding: `${t.sp24}px`, background: `${t.success}06`,
        borderRadius: t.r12, border: `1px solid ${t.success}10`,
        textAlign: "center",
      }}>
        <span style={{ fontFamily: font.mono, fontSize: 24, fontWeight: 800, color: t.success }}>{a.line}</span>
        <div style={{
          fontSize: 12, color: t.textBody, marginTop: t.sp8,
          fontFamily: font.display, lineHeight: 1.5,
        }}>
          Edge suggests this line is <strong style={{ color: t.success }}>+{a.edge}%</strong> favorable
        </div>
      </div>
    </div>
  );

  // Mobile: Bottom Sheet (Section 04)
  if (isMobile) {
    return (
      <div style={{ position: "fixed", inset: 0, zIndex: 100 }} role="dialog" aria-modal="true" aria-label="Edge Breakdown">
        <div className="backdrop-enter" onClick={onClose}
          style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)" }} />
        <div ref={panelRef} className="slide-up" style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          background: t.elevated, borderRadius: `${t.r16}px ${t.r16}px 0 0`,
          border: `1px solid rgba(255,255,255,0.08)`, borderBottom: "none",
          maxHeight: "85vh", display: "flex", flexDirection: "column",
          boxShadow: t.sheetShadow,
        }}>
          {/* Drag handle — required per Material Design bottom sheet */}
          <div style={{ display: "flex", justifyContent: "center", padding: `${t.sp12}px 0 ${t.sp4}px` }}>
            <div style={{ width: 32, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.15)" }} />
          </div>
          <div style={{
            padding: `${t.sp8}px ${t.sp24}px ${t.sp12}px`,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: `1px solid ${t.textBorder}`,
          }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: t.textPrimary, fontFamily: font.display }}>Edge Breakdown</span>
            <button onClick={onClose} aria-label="Close"
              style={{
                width: 32, height: 32, borderRadius: "50%", border: "none",
                background: "rgba(255,255,255,0.06)", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                minHeight: t.minTap, minWidth: t.minTap,
                padding: 0,
              }}>
              <svg width="14" height="14" viewBox="0 0 14 14">
                <path d="M3 3L11 11M11 3L3 11" stroke={t.textCaption} strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <div className="hide-scroll" style={{ flex: 1, overflowY: "auto", padding: `${t.sp16}px ${t.sp24}px ${t.sp32}px` }}>
            {content}
          </div>
        </div>
      </div>
    );
  }

  // Desktop: Centered Modal
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center" }}
      role="dialog" aria-modal="true" aria-label="Edge Breakdown">
      <div className="backdrop-enter" onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)" }} />
      <div ref={panelRef} className="modal-enter" style={{
        position: "relative", background: t.elevated,
        borderRadius: t.r16, border: `1px solid rgba(255,255,255,0.08)`,
        width: "90%", maxWidth: 560, maxHeight: "85vh",
        display: "flex", flexDirection: "column",
        boxShadow: t.modalShadow,
      }}>
        <div style={{
          padding: `${t.sp16}px ${t.sp24}px`,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          borderBottom: `1px solid ${t.textBorder}`, flexShrink: 0,
        }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: t.textPrimary, fontFamily: font.display }}>Edge Breakdown</span>
          <button onClick={onClose} aria-label="Close"
            style={{
              width: 36, height: 36, borderRadius: "50%", border: "none",
              background: "rgba(255,255,255,0.06)", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              minHeight: t.minTap, minWidth: t.minTap, padding: 0,
            }}>
            <svg width="14" height="14" viewBox="0 0 14 14">
              <path d="M3 3L11 11M11 3L3 11" stroke={t.textCaption} strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div className="custom-scroll" style={{ flex: 1, overflowY: "auto", padding: `${t.sp24}px` }}>
          {content}
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════
// FILTER BAR — 44px tap targets
// ═══════════════════════════════════════

function FilterBar({ activeFilter, onFilter }) {
  const filters = [
    { id: "all",    label: "All Chirps" },
    { id: "strong", label: "Strong", color: t.strong, icon: "\uD83D\uDD34" },
    { id: "chirp",  label: "Chirp",  color: t.chirp,  icon: "\uD83D\uDFE1" },
    { id: "soft",   label: "Soft",   color: t.soft,   icon: "\uD83D\uDD35" },
  ];

  return (
    <div role="tablist" aria-label="Filter by alert level" style={{
      display: "flex", alignItems: "center", gap: t.sp8,
      marginBottom: t.sp16,
    }}>
      {filters.map((f) => {
        const active = activeFilter === f.id;
        return (
          <div
            key={f.id}
            className="filter-btn"
            role="tab"
            tabIndex={0}
            aria-selected={active}
            aria-label={`Filter: ${f.label}`}
            onClick={() => onFilter(f.id)}
            onKeyDown={(e) => { if (e.key === "Enter") onFilter(f.id); }}
            style={{
              padding: `0 ${t.sp12}px`,
              borderRadius: t.r8,
              fontSize: 11, fontWeight: active ? 600 : 500,
              color: active ? (f.color || t.textPrimary) : t.textCaption,
              background: active ? `${f.color || t.textPrimary}10` : "transparent",
              border: `1px solid ${active ? `${f.color || t.textPrimary}20` : "transparent"}`,
              fontFamily: font.display,
              justifyContent: "center",
            }}
          >
            {f.icon && <span style={{ marginRight: 4 }}>{f.icon}</span>}
            {f.label}
          </div>
        );
      })}
    </div>
  );
}


// ═══════════════════════════════════════
// MAIN CHIRPS SCREEN
// ═══════════════════════════════════════

export default function ChirpsScreen() {
  const [expandedId, setExpandedId] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelAlert, setPanelAlert] = useState(null);
  const [activeTab, setActiveTab] = useState("chirps");
  const [activeFilter, setActiveFilter] = useState("all");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    injectCSS();
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // --- Mock Data (will be replaced with /api/alerts) ---
  const alerts = [
    {
      id: "c1", level: "strong", edge: 14.2, confidence: 87,
      t1: "NYY", t2: "BOS", s1: 4, s2: 2, inn: 6, top: true, outs: 1,
      balls: 2, strikes: 1,
      bases: [true, false, true],
      bat: { name: "A. Judge", avg: ".312", iso: ".290", hr: 22 },
      pit: { name: "C. Sale", era: "3.89", pc: 94, velo: "-2.1" },
      wind: { dir: "out", mph: 14 }, temp: "72\u00B0F",
      venue: "Fenway Park", pf: 104, line: "OVER 8.5", time: "2m ago",
      factors: [
        { name: "Judge elite power vs LHP", mult: "1.40x", pct: 85, color: t.accent, detail: "ISO .290 \u00B7 22 HR in 68 G \u00B7 vs LHP .341" },
        { name: "Pitcher fatigue detected", mult: "1.35x", pct: 78, color: t.danger, detail: "94 pitches \u00B7 velo down 2.1 mph \u00B7 slider flat" },
        { name: "Wind blowing out to CF", mult: "1.25x", pct: 65, color: t.success, detail: "14 mph to CF \u00B7 Fenway Green Monster" },
        { name: "Hitter-friendly park factor", mult: "1.15x", pct: 55, color: t.warning, detail: "Fenway PF 104 \u00B7 HR factor 112" },
        { name: "High-leverage runner position", mult: "1.20x", pct: 70, color: t.info, detail: "RE24: 1st & 3rd, 1 out = 1.54 expected runs" },
      ],
    },
    {
      id: "c2", level: "chirp", edge: 8.7, confidence: 68,
      t1: "LAD", t2: "SF", s1: 1, s2: 3, inn: 4, top: false, outs: 2,
      balls: 0, strikes: 2,
      bases: [false, true, false],
      bat: { name: "M. Betts", avg: ".289", iso: ".245", hr: 18 },
      pit: { name: "L. Webb", era: "3.12", pc: 61, velo: "+0.3" },
      wind: { dir: "cross", mph: 8 }, temp: "64\u00B0F",
      venue: "Oracle Park", pf: 95, line: "UNDER 7.0", time: "8m ago",
      factors: [
        { name: "Betts vs sinkerball", mult: "1.20x", pct: 60, color: t.accent, detail: "ISO .245 \u00B7 pulls 43% \u00B7 sinker .189 BA" },
        { name: "Webb pitch efficiency", mult: "1.15x", pct: 55, color: t.danger, detail: "61 pitches thru 4 \u00B7 slider 34% whiff" },
      ],
    },
    {
      id: "c3", level: "soft", edge: 5.1, confidence: 52,
      t1: "ATL", t2: "PHI", s1: 0, s2: 0, inn: 0, top: true, outs: 0,
      balls: 0, strikes: 0,
      bases: [false, false, false],
      bat: { name: "\u2014", avg: "\u2014", iso: "\u2014", hr: "\u2014" },
      pit: { name: "M. Fried", era: "2.65", pc: 0, velo: "\u2014" },
      wind: { dir: "out", mph: 11 }, temp: "78\u00B0F",
      venue: "Citizens Bank Park", pf: 108, line: "OVER 9.0", time: "Pre-game",
      factors: [
        { name: "Wind + park combo", mult: "1.18x", pct: 58, color: t.success, detail: "11 mph out \u00B7 CBP PF 108 \u00B7 HR factor 118" },
        { name: "Hot temperature", mult: "1.10x", pct: 45, color: t.warning, detail: "78\u00B0F \u00B7 ball carries +3% distance" },
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

  const filteredAlerts = activeFilter === "all"
    ? alerts
    : alerts.filter((a) => a.level === activeFilter);

  const activeEdges = alerts.length;
  const liveCount = liveGames.filter((g) => g.inn).length;

  const openPanel = useCallback((alert) => {
    setPanelAlert(alert);
    setPanelOpen(true);
  }, []);

  const closePanel = useCallback(() => {
    setPanelOpen(false);
  }, []);

  return (
    <div style={{
      minHeight: "100vh",
      background: t.bg,
      color: t.textPrimary,
      fontFamily: font.display,
    }}>
      {/* Sidebar (desktop) */}
      {!isMobile && <Sidebar activeTab={activeTab} onTabChange={setActiveTab} alertCount={activeEdges} />}

      {/* Mobile header */}
      {isMobile && <MobileHeader alertCount={activeEdges} />}

      {/* Main Content */}
      <div style={{
        marginLeft: isMobile ? 0 : 220,
        minHeight: "100vh",
        display: "flex", flexDirection: "column",
      }}>

        {/* Desktop Top Bar */}
        {!isMobile && (
          <header style={{
            padding: `${t.sp16}px ${t.sp32}px`,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: `1px solid ${t.textBorder}`,
            background: "rgba(13,13,13,0.6)",
            backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
            position: "sticky", top: 0, zIndex: 30,
            minHeight: t.minTap,
          }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, letterSpacing: "-0.03em" }}>Chirps</h1>
              <p style={{ fontSize: 12, color: t.textCaption, margin: "2px 0 0" }}>
                {activeEdges} active edge{activeEdges !== 1 ? "s" : ""} &middot; {liveCount} live game{liveCount !== 1 ? "s" : ""}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: t.sp8 }}>
              <div className="pulse-dot" style={{
                width: 6, height: 6, borderRadius: "50%", background: t.success,
                boxShadow: "0 0 6px rgba(34,197,94,0.4)",
              }} />
              <span style={{ fontSize: 11, fontWeight: 600, color: t.success }}>{liveCount} LIVE</span>
            </div>
          </header>
        )}

        {/* Content */}
        <main className="custom-scroll" style={{
          flex: 1, overflowY: "auto",
          padding: isMobile ? `${t.sp16}px ${t.sp16}px 80px` : `${t.sp24}px ${t.sp32}px ${t.sp32}px`,
        }}>

          {/* Mobile title */}
          {isMobile && (
            <div className="fade-in" style={{ marginBottom: t.sp16 }}>
              <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, letterSpacing: "-0.03em" }}>Chirps</h1>
              <p style={{ fontSize: 12, color: t.textCaption, margin: `${t.sp4}px 0 0` }}>
                {activeEdges} active edge{activeEdges !== 1 ? "s" : ""} &middot; {liveCount} live game{liveCount !== 1 ? "s" : ""}
              </p>
            </div>
          )}

          {/* Desktop Summary Stats */}
          {!isMobile && (
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: t.sp12,
              marginBottom: t.sp24,
            }}>
              <StatBox label="ACTIVE EDGES" value={activeEdges} color={t.textPrimary} sub="across all games" />
              <StatBox label="STRONG CHIRPS" value={alerts.filter(a => a.level === "strong").length} color={t.strong} sub="high confidence" />
              <StatBox label="LIVE GAMES" value={liveCount} color={t.success} sub="being scanned" />
              <StatBox label="AVG EDGE" value={`${(alerts.reduce((s, a) => s + a.edge, 0) / alerts.length).toFixed(1)}%`} color={t.chirp} sub="across all chirps" />
            </div>
          )}

          {/* Scoreboard Strip */}
          <ScoreboardStrip games={liveGames} />

          {/* Filter Bar */}
          <div style={{ paddingTop: t.sp12 }}>
            <FilterBar activeFilter={activeFilter} onFilter={setActiveFilter} />
          </div>

          {/* Chirp Cards Grid */}
          {filteredAlerts.length > 0 ? (
            <div className="chirps-grid">
              {filteredAlerts.map((alert) => (
                <ChirpCard
                  key={alert.id}
                  alert={alert}
                  level={alert.level}
                  expanded={expandedId === alert.id}
                  onToggle={() => setExpandedId(expandedId === alert.id ? null : alert.id)}
                  onTapLine={() => openPanel(alert)}
                />
              ))}
              <ScanningCard label="Scanning CHC @ STL..." />
            </div>
          ) : (
            <EmptyState />
          )}
        </main>
      </div>

      {/* Mobile Bottom Nav — always visible (Section 04) */}
      {isMobile && <MobileBottomNav activeTab={activeTab} onTabChange={setActiveTab} alertCount={activeEdges} />}

      {/* Edge Breakdown — bottom sheet on mobile, modal on desktop */}
      <EdgeBreakdownPanel
        open={panelOpen}
        onClose={closePanel}
        alert={panelAlert}
        isMobile={isMobile}
      />
    </div>
  );
}
