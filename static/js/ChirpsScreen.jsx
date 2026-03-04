import React, { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// CHIRP.BET — CHIRPS SCREEN (Web App Redesign)
// Responsive desktop-first layout with sidebar, grid cards, modals
// ═══════════════════════════════════════════════════════════════

// --- Data ---
const ESPN_LOGO = (id) =>
  `https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/${id}.png&h=80&w=80`;

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

// --- Design Tokens ---
const t = {
  // Surfaces
  bg:       "#06080C",
  surface:  "#0C1017",
  card:     "#10141C",
  elevated: "#161C28",
  hover:    "#1A2030",
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
  purple: "#8B5CF6",
  // Accent backgrounds
  redBg:    "rgba(239,68,68,0.06)",
  amberBg:  "rgba(245,158,11,0.06)",
  blueBg:   "rgba(59,130,246,0.06)",
  greenBg:  "rgba(34,197,94,0.05)",
  cyanBg:   "rgba(6,182,212,0.05)",
  purpleBg: "rgba(139,92,246,0.05)",
  // Radius
  r:  14,
  rs: 10,
  rl: 18,
  // Shadows
  cardShadow: "0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)",
  elevShadow: "0 4px 16px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
  modalShadow: "0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06)",
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
const CSS_ID = "chirps-web-css";
const injectCSS = () => {
  if (typeof document === "undefined" || document.getElementById(CSS_ID)) return;
  const el = document.createElement("style");
  el.id = CSS_ID;
  el.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.25s ease-out both; }

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

    @keyframes modalIn {
      from { opacity: 0; transform: scale(0.96) translateY(8px); }
      to   { opacity: 1; transform: scale(1) translateY(0); }
    }
    .modal-enter { animation: modalIn 0.2s cubic-bezier(0.16, 1, 0.3, 1); }

    @keyframes backdropIn {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    .backdrop-enter { animation: backdropIn 0.15s ease-out; }

    .hide-scroll::-webkit-scrollbar { display: none; }
    .hide-scroll { scrollbar-width: none; }

    .chirp-card {
      transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
      cursor: default;
    }
    .chirp-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.08);
    }

    .tap-target {
      cursor: pointer;
      transition: background 0.15s ease, color 0.15s ease;
      user-select: none;
    }
    .tap-target:hover {
      background: rgba(255,255,255,0.04) !important;
    }
    .tap-target:active {
      background: rgba(255,255,255,0.06) !important;
    }

    .nav-item {
      transition: background 0.15s ease, color 0.15s ease;
      cursor: pointer;
      user-select: none;
    }
    .nav-item:hover {
      background: rgba(255,255,255,0.04);
    }
    .nav-item.active {
      background: rgba(255,255,255,0.06);
    }

    .scoreboard-chip {
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      cursor: pointer;
    }
    .scoreboard-chip:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }

    .filter-btn {
      transition: all 0.15s ease;
      cursor: pointer;
      user-select: none;
    }
    .filter-btn:hover {
      background: rgba(255,255,255,0.06) !important;
    }

    /* Responsive grid */
    .chirps-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: 1fr;
    }
    @media (min-width: 900px) {
      .chirps-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    @media (min-width: 1400px) {
      .chirps-grid {
        grid-template-columns: repeat(3, 1fr);
      }
    }

    /* Scrollbar for sidebar */
    .custom-scroll::-webkit-scrollbar { width: 4px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,0.08);
      border-radius: 2px;
    }
    .custom-scroll::-webkit-scrollbar-thumb:hover {
      background: rgba(255,255,255,0.15);
    }
  `;
  document.head.appendChild(el);
};


// ═══════════════════════════════════════
// ICONS (SVG)
// ═══════════════════════════════════════

function IconGames({ size = 18, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2C6.5 2 2 6.5 2 12" strokeDasharray="4 2" />
      <path d="M8 2.5C6 6 6 18 8 21.5" />
      <path d="M16 2.5C18 6 18 18 16 21.5" />
    </svg>
  );
}

function IconChirps({ size = 18, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  );
}

function IconHistory({ size = 18, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3v5h5" />
      <path d="M3.05 13A9 9 0 1 0 6 5.3L3 8" />
      <path d="M12 7v5l4 2" />
    </svg>
  );
}

function IconSettings({ size = 18, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}

function IconClose({ size = 16, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round">
      <path d="M3 3L13 13M13 3L3 13" />
    </svg>
  );
}

function IconChevron({ size = 12, color = "currentColor", direction = "down" }) {
  const rotate = { down: 0, up: 180, left: 90, right: -90 }[direction];
  return (
    <svg width={size} height={size} viewBox="0 0 12 12"
      style={{ transition: "transform 0.2s", transform: `rotate(${rotate}deg)` }}>
      <path d="M2 4.5L6 8.5L10 4.5" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function IconFilter({ size = 14, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  );
}


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
  const d = size * 0.13;
  const pos = [
    { x: size * 0.85, y: m },
    { x: m, y: size * 0.15 },
    { x: size * 0.15, y: m },
  ];
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <polygon
        points={`${m},${size * 0.15} ${size * 0.85},${m} ${m},${size * 0.85} ${size * 0.15},${m}`}
        fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="0.8"
      />
      <rect
        x={m - d / 2} y={size * 0.85 - d / 2} width={d} height={d}
        fill={t.elevated} stroke="rgba(255,255,255,0.12)" strokeWidth="0.6"
        transform={`rotate(45 ${m} ${size * 0.85})`}
      />
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

function Badge({ label, color = "green", pulse = false, size = "sm" }) {
  const colors = { red: t.red, green: t.green, blue: t.blue, amber: t.amber, cyan: t.cyan, purple: t.purple };
  const c = colors[color] || color;
  const px = size === "lg" ? "10px 14px" : "3px 8px";
  const fs = size === "lg" ? 11 : 10;
  return (
    <span className={pulse ? "pulse-dot" : ""} style={{
      display: "inline-flex", alignItems: "center",
      padding: px, borderRadius: 6,
      background: `${c}10`, border: `1px solid ${c}18`,
      fontSize: fs, fontWeight: 600, color: c,
      letterSpacing: "0.02em", ...fontDisplay,
      whiteSpace: "nowrap",
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

function StatBox({ label, value, color = t.white, sub }) {
  return (
    <div style={{
      padding: "14px 16px",
      background: t.card,
      border: `1px solid ${t.border}`,
      borderRadius: t.rs,
    }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: t.muted, letterSpacing: "0.04em", ...fontDisplay, marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ ...fontMono, fontSize: 24, fontWeight: 800, color, letterSpacing: "-0.03em" }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 10, color: t.secondary, ...fontDisplay, marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════
// SIDEBAR NAVIGATION
// ═══════════════════════════════════════

function Sidebar({ activeTab, onTabChange, alertCount }) {
  const navItems = [
    { id: "games",    label: "Games",    icon: IconGames },
    { id: "chirps",   label: "Chirps",   icon: IconChirps, badge: alertCount },
    { id: "history",  label: "History",  icon: IconHistory },
    { id: "settings", label: "Settings", icon: IconSettings },
  ];

  return (
    <aside style={{
      width: 220,
      height: "100vh",
      position: "fixed",
      left: 0,
      top: 0,
      background: t.surface,
      borderRight: `1px solid ${t.border}`,
      display: "flex",
      flexDirection: "column",
      zIndex: 40,
    }}>
      {/* Logo */}
      <div style={{
        padding: "20px 20px 16px",
        borderBottom: `1px solid ${t.borderSubtle}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: "linear-gradient(135deg, #EF4444 0%, #F59E0B 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 8px rgba(239,68,68,0.2)",
          }}>
            <span style={{ fontSize: 16 }}>&#x1F997;</span>
          </div>
          <div>
            <span style={{
              fontSize: 18, fontWeight: 800, color: t.white, letterSpacing: "-0.02em",
              ...fontDisplay, display: "block", lineHeight: 1,
            }}>chirp</span>
            <span style={{
              fontSize: 9, fontWeight: 600, color: t.dim, ...fontDisplay,
              letterSpacing: "0.06em",
            }}>BETA</span>
          </div>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ flex: 1, padding: "12px 10px", overflow: "hidden" }}>
        {navItems.map((item) => {
          const active = activeTab === item.id;
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className="nav-item"
              onClick={() => onTabChange(item.id)}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px",
                borderRadius: 8,
                marginBottom: 2,
                background: active ? "rgba(255,255,255,0.06)" : "transparent",
                position: "relative",
              }}
            >
              <Icon size={18} color={active ? t.white : t.muted} />
              <span style={{
                fontSize: 13, fontWeight: active ? 600 : 500,
                color: active ? t.white : t.secondary,
                ...fontDisplay, flex: 1,
              }}>{item.label}</span>
              {item.badge > 0 && (
                <div style={{
                  minWidth: 18, height: 18, borderRadius: 9,
                  background: t.red,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 0 6px rgba(239,68,68,0.3)",
                }}>
                  <span style={{ fontSize: 9, fontWeight: 800, color: "#fff" }}>{item.badge}</span>
                </div>
              )}
              {active && (
                <div style={{
                  position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)",
                  width: 3, height: 20, borderRadius: 2,
                  background: t.blue,
                }} />
              )}
            </div>
          );
        })}
      </nav>

      {/* Live Status */}
      <div style={{
        padding: "14px 20px",
        borderTop: `1px solid ${t.borderSubtle}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div className="pulse-dot" style={{
            width: 6, height: 6, borderRadius: "50%", background: t.green,
            boxShadow: "0 0 6px rgba(34,197,94,0.4)",
          }} />
          <span style={{ fontSize: 11, fontWeight: 600, color: t.green, ...fontDisplay }}>
            LIVE
          </span>
          <span style={{ fontSize: 10, color: t.muted, ...fontDisplay, marginLeft: "auto" }}>
            Scanning
          </span>
        </div>
      </div>
    </aside>
  );
}


// ═══════════════════════════════════════
// MOBILE TOP BAR (shown on small screens)
// ═══════════════════════════════════════

function MobileHeader({ alertCount }) {
  return (
    <header style={{
      padding: "12px 16px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      borderBottom: `1px solid ${t.borderSubtle}`,
      background: "rgba(6,8,12,0.95)",
      backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
      position: "sticky", top: 0, zIndex: 50,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: "linear-gradient(135deg, #EF4444 0%, #F59E0B 100%)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: 14 }}>&#x1F997;</span>
        </div>
        <span style={{ fontSize: 17, fontWeight: 800, color: t.white, ...fontDisplay }}>chirp</span>
        <span style={{
          fontSize: 9, fontWeight: 600, color: t.dim,
          background: "rgba(255,255,255,0.04)", padding: "2px 6px", borderRadius: 4,
        }}>BETA</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {alertCount > 0 && (
          <div style={{
            minWidth: 20, height: 20, borderRadius: 10,
            background: t.red, display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ fontSize: 10, fontWeight: 800, color: "#fff" }}>{alertCount}</span>
          </div>
        )}
        <div className="pulse-dot" style={{
          width: 6, height: 6, borderRadius: "50%", background: t.green,
          boxShadow: "0 0 4px rgba(34,197,94,0.4)",
        }} />
        <span style={{ fontSize: 10, fontWeight: 600, color: t.green, ...fontDisplay }}>LIVE</span>
      </div>
    </header>
  );
}


// ═══════════════════════════════════════
// MOBILE BOTTOM NAV (shown on small screens)
// ═══════════════════════════════════════

function MobileBottomNav({ activeTab, onTabChange, alertCount }) {
  const items = [
    { id: "games",    icon: IconGames,    label: "Games" },
    { id: "chirps",   icon: IconChirps,   label: "Chirps", badge: alertCount },
    { id: "history",  icon: IconHistory,  label: "History" },
    { id: "settings", icon: IconSettings, label: "Settings" },
  ];

  return (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0,
      background: "rgba(6,8,12,0.95)",
      backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
      borderTop: `1px solid ${t.borderSubtle}`,
      padding: "6px 0 env(safe-area-inset-bottom, 12px)",
      display: "flex", justifyContent: "space-around",
      zIndex: 50,
    }}>
      {items.map((item) => {
        const active = activeTab === item.id;
        const Icon = item.icon;
        return (
          <div
            key={item.id}
            onClick={() => onTabChange(item.id)}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
              padding: "6px 16px", position: "relative", minWidth: 52,
              borderRadius: 8, cursor: "pointer",
            }}
          >
            <Icon size={18} color={active ? t.white : t.dim} />
            <span style={{
              fontSize: 9, fontWeight: active ? 700 : 500,
              color: active ? t.white : t.dim, ...fontDisplay,
            }}>{item.label}</span>
            {item.badge > 0 && (
              <div style={{
                position: "absolute", top: 0, right: 6,
                minWidth: 14, height: 14, borderRadius: 7,
                background: t.red,
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 0 6px rgba(239,68,68,0.35)",
              }}>
                <span style={{ fontSize: 8, fontWeight: 800, color: "#fff" }}>{item.badge}</span>
              </div>
            )}
          </div>
        );
      })}
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
        display: "flex", gap: 10, overflowX: "auto",
        padding: "0 0 16px",
        borderBottom: `1px solid ${t.border}`,
        marginBottom: 8,
      }}
    >
      {games.map((g, i) => (
        <div key={i} className="scoreboard-chip" style={{
          flexShrink: 0, minWidth: 130,
          background: t.card,
          border: `1px solid ${g.chirp ? `${levelColor[g.level]}25` : t.border}`,
          borderRadius: t.rs,
          borderLeft: g.chirp ? `3px solid ${levelColor[g.level]}` : `1px solid ${t.border}`,
          boxShadow: t.cardShadow,
          opacity: g.chirp ? 1 : 0.55,
        }}>
          <div style={{ padding: "10px 12px" }}>
            {[{ team: g.a, score: g.as }, { team: g.h, score: g.hs }].map((row, j) => (
              <div key={j} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                marginBottom: j === 0 ? 4 : 0,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <TeamLogo team={row.team} size={16} />
                  <span style={{ fontSize: 11, fontWeight: 700, color: t.primary, ...fontDisplay }}>
                    {TEAMS[row.team]?.abbr}
                  </span>
                </div>
                {g.inn && (
                  <span style={{ ...fontMono, fontSize: 12, fontWeight: 800, color: t.white }}>
                    {row.score}
                  </span>
                )}
              </div>
            ))}
            <div style={{
              marginTop: 6, display: "flex", alignItems: "center", justifyContent: "space-between",
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
// CHIRP CARD
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

  return (
    <div className="chirp-card fade-in" style={{
      background: t.card,
      border: `1px solid ${t.border}`,
      borderRadius: t.r,
      borderLeft: `3px solid ${cfg.color}`,
      boxShadow: level === "strong"
        ? `0 2px 20px rgba(0,0,0,0.35), 0 0 0 1px ${cfg.color}10`
        : t.cardShadow,
      overflow: "hidden",
    }}>
      <div style={{ padding: "18px 18px 0" }}>

        {/* Header: Level + Edge % */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 14,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Badge label={cfg.label} color={level === "strong" ? "red" : level === "chirp" ? "amber" : "blue"} pulse={level === "strong"} />
            <span style={{
              ...fontMono, fontSize: level === "strong" ? 28 : 22,
              fontWeight: 800, color: cfg.color, letterSpacing: "-0.03em",
            }}>
              +{a.edge}%
            </span>
          </div>
          <span style={{ fontSize: 10, color: t.muted, ...fontDisplay }}>{a.time}</span>
        </div>

        {/* Scoreboard */}
        <div style={{
          padding: isLive ? "14px 16px" : "12px 16px",
          background: "rgba(255,255,255,0.02)",
          borderRadius: t.rs,
          border: `1px solid ${t.borderSubtle}`,
          marginBottom: 14,
        }}>
          <div style={{ display: "flex", alignItems: "center" }}>
            {/* Away */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10 }}>
              <TeamLogo team={a.t1} size={isLive ? 32 : 28} />
              <div>
                <span style={{
                  fontSize: 14, fontWeight: 700, color: t.white,
                  ...fontDisplay, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t1]?.abbr}</span>
                <span style={{
                  fontSize: 10, color: t.muted, ...fontDisplay,
                }}>{TEAMS[a.t1]?.name}</span>
              </div>
              {isLive && (
                <span style={{
                  ...fontMono, fontSize: 26, fontWeight: 800, color: t.white,
                  marginLeft: "auto", letterSpacing: "-0.03em",
                }}>{a.s1}</span>
              )}
            </div>

            {/* Center */}
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 4, margin: "0 16px", flexShrink: 0,
            }}>
              {isLive ? (
                <>
                  <Diamond bases={a.bases} size={40} />
                  <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <div className="pulse-dot" style={{
                      width: 4, height: 4, borderRadius: "50%", background: t.green,
                    }} />
                    <span style={{
                      fontSize: 10, fontWeight: 700, color: t.green, ...fontDisplay,
                    }}>{a.top ? "\u25B2" : "\u25BC"}{ordinal(a.inn)}</span>
                    <OutDots count={a.outs} />
                  </div>
                </>
              ) : (
                <span style={{
                  fontSize: 12, fontWeight: 600, color: t.muted, ...fontDisplay,
                }}>@ 7:10 PM</span>
              )}
            </div>

            {/* Home */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10, flexDirection: "row-reverse" }}>
              <TeamLogo team={a.t2} size={isLive ? 32 : 28} />
              <div style={{ textAlign: "right" }}>
                <span style={{
                  fontSize: 14, fontWeight: 700, color: t.white,
                  ...fontDisplay, display: "block", lineHeight: 1,
                }}>{TEAMS[a.t2]?.abbr}</span>
                <span style={{
                  fontSize: 10, color: t.muted, ...fontDisplay,
                }}>{TEAMS[a.t2]?.name}</span>
              </div>
              {isLive && (
                <span style={{
                  ...fontMono, fontSize: 26, fontWeight: 800, color: t.white,
                  marginRight: "auto", letterSpacing: "-0.03em",
                }}>{a.s2}</span>
              )}
            </div>
          </div>
        </div>

        {/* Matchup Context */}
        {isLive && level !== "soft" && (
          <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
            <div style={{
              flex: 1, padding: "10px 12px", borderRadius: 8,
              background: t.blueBg, border: "1px solid rgba(59,130,246,0.08)",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.blue, letterSpacing: "0.04em", ...fontDisplay }}>AT BAT</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.white, ...fontDisplay, marginTop: 3 }}>{a.bat.name}</div>
              <div style={{ ...fontMono, fontSize: 10, color: t.secondary, marginTop: 2 }}>{a.bat.avg} / {a.bat.hr} HR</div>
            </div>
            <div style={{
              flex: 1, padding: "10px 12px", borderRadius: 8,
              background: t.redBg, border: "1px solid rgba(239,68,68,0.08)",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: t.red, letterSpacing: "0.04em", ...fontDisplay }}>PITCHING</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.white, ...fontDisplay, marginTop: 3 }}>{a.pit.name}</div>
              <div style={{ ...fontMono, fontSize: 10, color: t.secondary, marginTop: 2 }}>{a.pit.era} ERA / {a.pit.pc} pc</div>
            </div>
          </div>
        )}

        {/* Condition Tags */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 12 }}>
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
                borderRadius: 0,
              }}
            >
              <span style={{
                fontSize: 10, fontWeight: 700, color: t.muted,
                letterSpacing: "0.06em", ...fontDisplay,
              }}>WHY THIS CHIRP</span>
              <IconChevron size={12} color={t.dim} direction={expanded ? "up" : "down"} />
            </div>

            {expanded && (
              <div className="fade-in" style={{ paddingBottom: 10 }}>
                {a.factors.map((f, i) => (
                  <div key={i} style={{ marginBottom: 14 }}>
                    <div style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      marginBottom: 5,
                    }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: t.primary, ...fontDisplay }}>{f.name}</span>
                      <span style={{ ...fontMono, fontSize: 11, fontWeight: 700, color: f.color }}>{f.mult}</span>
                    </div>
                    <div style={{
                      height: 3, background: "rgba(255,255,255,0.04)",
                      borderRadius: 2, overflow: "hidden", marginBottom: 4,
                    }}>
                      <div style={{
                        height: "100%", width: `${f.pct}%`, background: f.color,
                        borderRadius: 2, transition: "width 0.5s ease-out",
                      }} />
                    </div>
                    <span style={{ fontSize: 10, color: t.muted, ...fontDisplay, lineHeight: 1.4 }}>{f.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Action Bar */}
      <div
        className="tap-target"
        onClick={onTapLine}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "14px 18px",
          background: t.greenBg,
          borderTop: `1px solid rgba(34,197,94,0.06)`,
          borderRadius: 0,
        }}
      >
        <div>
          <span style={{ fontSize: 11, color: t.secondary, ...fontDisplay }}>{a.venue}</span>
          <div style={{ fontSize: 9, color: t.muted, ...fontDisplay, marginTop: 2 }}>
            Click for full breakdown
          </div>
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
// SCANNING SKELETON CARD
// ═══════════════════════════════════════

function ScanningCard({ label }) {
  return (
    <div className="fade-in" style={{
      background: t.card,
      border: `1px solid ${t.border}`,
      borderRadius: t.r,
      boxShadow: t.cardShadow,
      padding: 18,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <div className="pulse-dot" style={{
          width: 6, height: 6, borderRadius: "50%", background: t.dim,
        }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: t.secondary, ...fontDisplay }}>
          {label}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <Skeleton w={28} h={28} r={14} />
        <Skeleton w={60} h={10} />
        <div style={{ flex: 1 }} />
        <Skeleton w={60} h={10} />
        <Skeleton w={28} h={28} r={14} />
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <Skeleton w={56} h={6} />
        <Skeleton w={68} h={6} />
        <Skeleton w={44} h={6} />
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
      textAlign: "center", padding: "48px 24px 32px",
      gridColumn: "1 / -1",
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: 16,
        background: "rgba(255,255,255,0.04)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginBottom: 14,
      }}>
        <span style={{ fontSize: 26 }}>&#x1F997;</span>
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: t.secondary, ...fontDisplay }}>
        All quiet for now
      </div>
      <div style={{ fontSize: 12, color: t.muted, marginTop: 6, ...fontDisplay, lineHeight: 1.6, maxWidth: 320, margin: "6px auto 0" }}>
        Edges surface here when conditions align.
        We're scanning every pitch across all live games.
      </div>
    </div>
  );
}


// ═══════════════════════════════════════
// MODAL (replaces BottomSheet for web)
// ═══════════════════════════════════════

function Modal({ open, onClose, title, children, width = 520 }) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handleEsc = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center" }}>
      {/* Backdrop */}
      <div
        className="backdrop-enter"
        onClick={onClose}
        style={{
          position: "absolute", inset: 0,
          background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)",
        }}
      />
      {/* Modal */}
      <div
        ref={modalRef}
        className="modal-enter"
        style={{
          position: "relative",
          background: t.surface,
          borderRadius: t.rl,
          border: `1px solid ${t.borderHover}`,
          width: "90%",
          maxWidth: width,
          maxHeight: "85vh",
          display: "flex", flexDirection: "column",
          boxShadow: t.modalShadow,
        }}
      >
        {/* Header */}
        {title && (
          <div style={{
            padding: "18px 24px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: `1px solid ${t.border}`,
            flexShrink: 0,
          }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: t.white, ...fontDisplay }}>{title}</span>
            <div
              onClick={onClose}
              className="tap-target"
              style={{
                width: 32, height: 32, borderRadius: "50%",
                background: "rgba(255,255,255,0.06)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              <IconClose size={14} color={t.muted} />
            </div>
          </div>
        )}
        {/* Content */}
        <div className="custom-scroll" style={{ flex: 1, overflowY: "auto", padding: "20px 24px 28px" }}>
          {children}
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════
// FILTER BAR
// ═══════════════════════════════════════

function FilterBar({ activeFilter, onFilter }) {
  const filters = [
    { id: "all",    label: "All Chirps" },
    { id: "strong", label: "Strong", color: t.red },
    { id: "chirp",  label: "Chirp",  color: t.amber },
    { id: "soft",   label: "Soft",   color: t.blue },
  ];

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 6,
      marginBottom: 16,
    }}>
      <IconFilter size={14} color={t.muted} />
      {filters.map((f) => {
        const active = activeFilter === f.id;
        return (
          <div
            key={f.id}
            className="filter-btn"
            onClick={() => onFilter(f.id)}
            style={{
              padding: "5px 12px",
              borderRadius: 6,
              fontSize: 11,
              fontWeight: active ? 600 : 500,
              color: active ? (f.color || t.white) : t.muted,
              background: active ? `${f.color || t.white}10` : "transparent",
              border: `1px solid ${active ? `${f.color || t.white}20` : "transparent"}`,
              ...fontDisplay,
            }}
          >
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
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAlert, setModalAlert] = useState(null);
  const [activeTab, setActiveTab] = useState("chirps");
  const [activeFilter, setActiveFilter] = useState("all");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    injectCSS();
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

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

  const filteredAlerts = activeFilter === "all"
    ? alerts
    : alerts.filter((a) => a.level === activeFilter);

  const activeEdges = alerts.length;
  const liveCount = liveGames.filter((g) => g.inn).length;

  const openModal = useCallback((alert) => {
    setModalAlert(alert);
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setModalOpen(false);
  }, []);

  // ── Layout ──
  return (
    <div style={{
      minHeight: "100vh",
      background: t.bg,
      color: t.white,
      ...fontDisplay,
    }}>
      {/* Sidebar (desktop only) */}
      {!isMobile && (
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} alertCount={activeEdges} />
      )}

      {/* Mobile header */}
      {isMobile && <MobileHeader alertCount={activeEdges} />}

      {/* Main Content Area */}
      <div style={{
        marginLeft: isMobile ? 0 : 220,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}>

        {/* Top Bar (desktop) */}
        {!isMobile && (
          <header style={{
            padding: "16px 32px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: `1px solid ${t.borderSubtle}`,
            background: "rgba(6,8,12,0.6)",
            backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
            position: "sticky", top: 0, zIndex: 30,
          }}>
            <div>
              <h1 style={{
                fontSize: 22, fontWeight: 800, margin: 0, letterSpacing: "-0.03em",
                ...fontDisplay,
              }}>Chirps</h1>
              <p style={{
                fontSize: 12, color: t.muted, margin: "2px 0 0", ...fontDisplay,
              }}>
                {activeEdges} active edge{activeEdges !== 1 ? "s" : ""} &middot; {liveCount} live game{liveCount !== 1 ? "s" : ""}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div className="pulse-dot" style={{
                  width: 6, height: 6, borderRadius: "50%", background: t.green,
                  boxShadow: "0 0 6px rgba(34,197,94,0.4)",
                }} />
                <span style={{ fontSize: 11, fontWeight: 600, color: t.green, ...fontDisplay }}>
                  {liveCount} LIVE
                </span>
              </div>
            </div>
          </header>
        )}

        {/* Content */}
        <main className="custom-scroll" style={{
          flex: 1,
          overflowY: "auto",
          padding: isMobile ? "16px 16px 80px" : "24px 32px 32px",
        }}>

          {/* Mobile page title */}
          {isMobile && (
            <div className="fade-in" style={{ marginBottom: 14 }}>
              <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, letterSpacing: "-0.03em" }}>Chirps</h1>
              <p style={{ fontSize: 12, color: t.muted, margin: "4px 0 0" }}>
                {activeEdges} active edge{activeEdges !== 1 ? "s" : ""} &middot; {liveCount} live game{liveCount !== 1 ? "s" : ""}
              </p>
            </div>
          )}

          {/* Summary Stats (desktop) */}
          {!isMobile && (
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12,
              marginBottom: 24,
            }}>
              <StatBox label="ACTIVE EDGES" value={activeEdges} color={t.white} sub="across all games" />
              <StatBox label="STRONG CHIRPS" value={alerts.filter(a => a.level === "strong").length} color={t.red} sub="high confidence" />
              <StatBox label="LIVE GAMES" value={liveCount} color={t.green} sub="being scanned" />
              <StatBox label="AVG EDGE" value={`${(alerts.reduce((s, a) => s + a.edge, 0) / alerts.length).toFixed(1)}%`} color={t.amber} sub="across all chirps" />
            </div>
          )}

          {/* Scoreboard Strip */}
          <ScoreboardStrip games={liveGames} />

          {/* Filter Bar */}
          <div style={{ paddingTop: 12 }}>
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
                  onTapLine={() => openModal(alert)}
                />
              ))}
              <ScanningCard label="Scanning CHC @ STL..." />
            </div>
          ) : (
            <EmptyState />
          )}

        </main>
      </div>

      {/* Mobile Bottom Nav */}
      {isMobile && (
        <MobileBottomNav activeTab={activeTab} onTabChange={setActiveTab} alertCount={activeEdges} />
      )}

      {/* Modal (Edge Breakdown) */}
      <Modal
        open={modalOpen}
        onClose={closeModal}
        title="Edge Breakdown"
        width={560}
      >
        {modalAlert && (
          <div>
            {/* Header */}
            <div style={{
              display: "flex", alignItems: "center", gap: 12, marginBottom: 24,
            }}>
              <Badge
                label={modalAlert.level === "strong" ? "STRONG CHIRP" : modalAlert.level === "chirp" ? "CHIRP" : "SOFT CHIRP"}
                color={modalAlert.level === "strong" ? "red" : modalAlert.level === "chirp" ? "amber" : "blue"}
                pulse={modalAlert.level === "strong"}
                size="lg"
              />
              <span style={{
                ...fontMono, fontSize: 26, fontWeight: 800,
                color: modalAlert.level === "strong" ? t.red : modalAlert.level === "chirp" ? t.amber : t.blue,
              }}>
                +{modalAlert.edge}%
              </span>
            </div>

            {/* Matchup */}
            <div style={{
              display: "flex", alignItems: "center", gap: 12, marginBottom: 24,
              padding: "14px 16px",
              background: "rgba(255,255,255,0.02)",
              borderRadius: t.rs,
              border: `1px solid ${t.borderSubtle}`,
            }}>
              <TeamLogo team={modalAlert.t1} size={28} />
              <span style={{ fontSize: 14, fontWeight: 700, color: t.white, ...fontDisplay }}>
                {TEAMS[modalAlert.t1]?.abbr}
              </span>
              {modalAlert.inn > 0 && (
                <span style={{ ...fontMono, fontSize: 18, fontWeight: 800, color: t.white }}>
                  {modalAlert.s1}
                </span>
              )}
              <span style={{ fontSize: 12, color: t.dim, margin: "0 4px" }}>vs</span>
              {modalAlert.inn > 0 && (
                <span style={{ ...fontMono, fontSize: 18, fontWeight: 800, color: t.white }}>
                  {modalAlert.s2}
                </span>
              )}
              <span style={{ fontSize: 14, fontWeight: 700, color: t.white, ...fontDisplay }}>
                {TEAMS[modalAlert.t2]?.abbr}
              </span>
              <TeamLogo team={modalAlert.t2} size={28} />
              <span style={{ marginLeft: "auto", fontSize: 11, color: t.muted, ...fontDisplay }}>
                {modalAlert.venue}
              </span>
            </div>

            {/* Factors */}
            <div style={{ marginBottom: 20 }}>
              <div style={{
                fontSize: 10, fontWeight: 700, color: t.muted, letterSpacing: "0.06em",
                ...fontDisplay, marginBottom: 14,
              }}>CONTRIBUTING FACTORS</div>
              {modalAlert.factors.map((f, i) => (
                <div key={i} style={{ marginBottom: 18 }}>
                  <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    marginBottom: 6,
                  }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: t.primary, ...fontDisplay }}>{f.name}</span>
                    <span style={{ ...fontMono, fontSize: 13, fontWeight: 700, color: f.color }}>{f.mult}</span>
                  </div>
                  <div style={{
                    height: 4, background: "rgba(255,255,255,0.04)",
                    borderRadius: 2, overflow: "hidden", marginBottom: 6,
                  }}>
                    <div style={{
                      height: "100%", width: `${f.pct}%`, background: f.color,
                      borderRadius: 2, transition: "width 0.6s ease-out",
                    }} />
                  </div>
                  <span style={{ fontSize: 11, color: t.muted, ...fontDisplay, lineHeight: 1.4 }}>{f.detail}</span>
                </div>
              ))}
            </div>

            {/* O/U Summary */}
            <div style={{
              padding: "20px 24px",
              background: t.greenBg,
              borderRadius: t.rs,
              border: "1px solid rgba(34,197,94,0.08)",
              textAlign: "center",
            }}>
              <span style={{ ...fontMono, fontSize: 24, fontWeight: 800, color: t.green }}>
                {modalAlert.line}
              </span>
              <div style={{
                fontSize: 12, color: t.secondary, marginTop: 8, ...fontDisplay, lineHeight: 1.5,
              }}>
                Edge suggests this line is <strong style={{ color: t.green }}>+{modalAlert.edge}%</strong> favorable
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
