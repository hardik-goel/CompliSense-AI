/**
 * Animated mini-diagrams for the platform feature cards.
 * Each fits the 80px `.card-visual` slot (viewBox 240x80) and uses SMIL
 * so it animates continuously without JS — matching the site's existing style.
 */

const svgProps = {
  width: "100%",
  height: 80,
  viewBox: "0 0 240 80",
  preserveAspectRatio: "xMidYMid meet" as const,
  xmlns: "http://www.w3.org/2000/svg",
};

/* AI Governance — model fans signals into controls, then to "Audit Ready" */
export function AiGovernanceViz() {
  return (
    <svg {...svgProps} fill="none">
      <g stroke="#1D4ED8" strokeWidth="1" opacity="0.45">
        <path d="M67,40 L130,20" />
        <path d="M67,40 L130,40" />
        <path d="M67,40 L130,62" />
      </g>
      <g stroke="#0E7490" strokeWidth="1" opacity="0.45">
        <path d="M150,20 L183,40" />
        <path d="M150,40 L183,40" />
        <path d="M150,62 L183,40" />
      </g>

      {/* signal packets flowing outward then converging */}
      <circle r="2.2" fill="#22D3EE"><animateMotion dur="1.8s" repeatCount="indefinite" path="M67,40 L130,20" /></circle>
      <circle r="2.2" fill="#22D3EE"><animateMotion dur="1.8s" begin="0.4s" repeatCount="indefinite" path="M67,40 L130,40" /></circle>
      <circle r="2.2" fill="#22D3EE"><animateMotion dur="1.8s" begin="0.8s" repeatCount="indefinite" path="M67,40 L130,62" /></circle>
      <circle r="2.4" fill="#22C55E"><animateMotion dur="1.6s" begin="1s" repeatCount="indefinite" path="M150,40 L183,40" /></circle>

      {/* model node + pulse */}
      <circle cx="52" cy="40" r="15" fill="#0D1A30" stroke="#3B82F6" strokeWidth="2" />
      <circle cx="52" cy="40" r="15" fill="none" stroke="#3B82F6" strokeWidth="1">
        <animate attributeName="r" values="15;25;15" dur="2.6s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.6;0;0.6" dur="2.6s" repeatCount="indefinite" />
      </circle>
      <text x="52" y="38" textAnchor="middle" fill="#3B82F6" fontSize="7" fontFamily="monospace">AI</text>
      <text x="52" y="46.5" textAnchor="middle" fill="#3B82F6" fontSize="7" fontFamily="monospace">Model</text>

      {/* control nodes */}
      <g fontFamily="monospace">
        <circle cx="140" cy="20" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.2" />
        <text x="140" y="22.5" textAnchor="middle" fill="#22D3EE" fontSize="5.8">Bias</text>
        <circle cx="140" cy="40" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.2" />
        <text x="140" y="42.5" textAnchor="middle" fill="#22D3EE" fontSize="5.8">Owner</text>
        <circle cx="140" cy="62" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.2" />
        <text x="140" y="64.5" textAnchor="middle" fill="#22D3EE" fontSize="5.8">Docs</text>
      </g>

      {/* output */}
      <circle cx="196" cy="40" r="13" fill="#0D1A30" stroke="#22C55E" strokeWidth="2" />
      <text x="196" y="38" textAnchor="middle" fill="#22C55E" fontSize="6" fontFamily="monospace">Audit</text>
      <text x="196" y="46" textAnchor="middle" fill="#22C55E" fontSize="6" fontFamily="monospace">Ready</text>
    </svg>
  );
}

/* Risk Assessments — live monitoring bars breathing under a risk cap */
export function RiskViz() {
  const bars = [
    { x: 40, color: "#EF4444", h: "18;40;18", y: "54;32;54", dur: "2.4s" },
    { x: 76, color: "#F59E0B", h: "30;52;30", y: "42;20;42", dur: "2.9s" },
    { x: 112, color: "#22C55E", h: "44;30;44", y: "28;42;28", dur: "2.2s" },
    { x: 148, color: "#3B82F6", h: "24;46;24", y: "48;26;48", dur: "3.1s" },
    { x: 184, color: "#8B5CF6", h: "36;20;36", y: "36;52;36", dur: "2.6s" },
  ];
  return (
    <svg {...svgProps}>
      <line x1="34" y1="24" x2="206" y2="24" stroke="#EF4444" strokeWidth="1" strokeDasharray="4 4" opacity="0.5" />
      <text x="210" y="27" textAnchor="end" fill="#EF4444" fontSize="6.5" fontFamily="monospace" opacity="0.7">cap</text>
      <line x1="34" y1="72" x2="206" y2="72" stroke="#1B3A5C" strokeWidth="1" />
      {bars.map((b) => (
        <rect key={b.x} x={b.x} width="22" rx="2.5" fill={b.color} opacity="0.85">
          <animate attributeName="height" values={b.h} dur={b.dur} repeatCount="indefinite" />
          <animate attributeName="y" values={b.y} dur={b.dur} repeatCount="indefinite" />
        </rect>
      ))}
      {/* live indicator */}
      <circle cx="40" cy="10" r="3" fill="#22C55E">
        <animate attributeName="opacity" values="1;0.2;1" dur="1.4s" repeatCount="indefinite" />
      </circle>
      <text x="48" y="13" fill="#64748B" fontSize="7" fontFamily="monospace">live</text>
    </svg>
  );
}

/* Policy Management — versioned doc, lines typing in, change diff + approval stamp */
export function PolicyViz() {
  return (
    <svg {...svgProps} fill="none">
      <rect x="74" y="12" width="84" height="58" rx="6" fill="#0D1A30" stroke="#1B3A5C" strokeWidth="1.4" />
      <path d="M148,12 L160,24 L148,24 Z" fill="#1B3A5C" />

      <g>
        <rect x="84" y="24" height="3" rx="1.5" fill="#3B82F6"><animate attributeName="width" values="0;46;46" dur="3s" repeatCount="indefinite" /></rect>
        <rect x="84" y="32" height="3" rx="1.5" fill="#475569"><animate attributeName="width" values="0;58;58" dur="3s" begin="0.3s" repeatCount="indefinite" /></rect>
        <rect x="84" y="40" height="3" rx="1.5" fill="#475569"><animate attributeName="width" values="0;38;38" dur="3s" begin="0.6s" repeatCount="indefinite" /></rect>
        <rect x="84" y="48" height="3" rx="1.5" fill="#22C55E"><animate attributeName="width" values="0;52;52" dur="3s" begin="0.9s" repeatCount="indefinite" /></rect>
      </g>

      {/* version badge */}
      <rect x="112" y="56" width="36" height="13" rx="6.5" fill="#0D1A30" stroke="#22C55E" strokeWidth="1" />
      <text x="130" y="65" textAnchor="middle" fill="#22C55E" fontSize="7.5" fontFamily="monospace">v3.0</text>

      {/* approval stamp pops in */}
      <g>
        <circle cx="166" cy="22" r="11" fill="#0D1A30" stroke="#22C55E" strokeWidth="1.6">
          <animate attributeName="r" values="0;0;11;11" dur="3s" repeatCount="indefinite" />
        </circle>
        <path d="M161,22 l3.4,3.4 l6,-7" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <animate attributeName="opacity" values="0;0;1;1" dur="3s" repeatCount="indefinite" />
        </path>
      </g>
    </svg>
  );
}

/* Audit Trails — append-only chain with a pulse writing across, padlocked */
export function AuditViz() {
  const blocks = [34, 84, 134, 184];
  return (
    <svg {...svgProps} fill="none">
      <line x1="47" y1="40" x2="197" y2="40" stroke="#1B3A5C" strokeWidth="2" />

      {/* padlock above the first block */}
      <rect x="42" y="18" width="10" height="7" rx="1.5" fill="#22D3EE" />
      <path d="M44,18 v-2 a3,3 0 0 1 6,0 v2" stroke="#22D3EE" strokeWidth="1.3" />

      {blocks.map((x, i) => (
        <g key={x} opacity={i === 3 ? undefined : 1}>
          {i === 3 && <animate attributeName="opacity" values="0;0;1;1" dur="3.6s" repeatCount="indefinite" />}
          <rect x={x} y="27" width="26" height="26" rx="5" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.4" />
          <rect x={x + 5} y="34" width="16" height="2.4" rx="1.2" fill="#22D3EE" opacity="0.55" />
          <rect x={x + 5} y="40" width="11" height="2.4" rx="1.2" fill="#22D3EE" opacity="0.35" />
          <rect x={x + 5} y="46" width="14" height="2.4" rx="1.2" fill="#22D3EE" opacity="0.35" />
          {i === 3 && (
            <rect x={x} y="27" width="26" height="26" rx="5" fill="none" stroke="#22C55E" strokeWidth="1.4">
              <animate attributeName="opacity" values="0;1;0" dur="1.8s" repeatCount="indefinite" />
            </rect>
          )}
        </g>
      ))}

      {/* write pulse travelling along the ledger */}
      <circle r="3.5" fill="#22D3EE">
        <animateMotion dur="3s" repeatCount="indefinite" path="M47,40 L197,40" />
        <animate attributeName="opacity" values="0;1;1;0" dur="3s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

/* Vendor Compliance — radar sweep scanning vendors for risk blips */
export function VendorViz() {
  return (
    <svg {...svgProps} fill="none">
      <g stroke="#1B3A5C" strokeWidth="1" opacity="0.7">
        <circle cx="120" cy="40" r="34" />
        <circle cx="120" cy="40" r="23" />
        <circle cx="120" cy="40" r="12" />
        <line x1="86" y1="40" x2="154" y2="40" />
        <line x1="120" y1="6" x2="120" y2="74" />
      </g>

      {/* sweep wedge + leading edge */}
      <path d="M120,40 L120,6 A34,34 0 0 1 137,11 Z" fill="#22D3EE" opacity="0.14">
        <animateTransform attributeName="transform" type="rotate" from="0 120 40" to="360 120 40" dur="4s" repeatCount="indefinite" />
      </path>
      <line x1="120" y1="40" x2="120" y2="6" stroke="#22D3EE" strokeWidth="1.5" opacity="0.85">
        <animateTransform attributeName="transform" type="rotate" from="0 120 40" to="360 120 40" dur="4s" repeatCount="indefinite" />
      </line>

      {/* vendor blips lighting up as the sweep passes */}
      <circle cx="142" cy="24" r="2.6" fill="#22C55E"><animate attributeName="opacity" values="0;1;0" dur="4s" begin="0.5s" repeatCount="indefinite" /></circle>
      <circle cx="100" cy="54" r="2.6" fill="#F59E0B"><animate attributeName="opacity" values="0;1;0" dur="4s" begin="2s" repeatCount="indefinite" /></circle>
      <circle cx="135" cy="57" r="2.6" fill="#EF4444"><animate attributeName="opacity" values="0;1;0" dur="4s" begin="3s" repeatCount="indefinite" /></circle>

      <circle cx="120" cy="40" r="2.5" fill="#22D3EE" />
    </svg>
  );
}

/* DPDP Compliance — obligations tick off as a readiness ring fills */
export function DpdpViz() {
  const rows = [18, 40, 62];
  return (
    <svg {...svgProps} fill="none">
      {rows.map((y, i) => (
        <g key={y}>
          <rect x="22" y={y - 6.5} width="13" height="13" rx="3" fill="#0D1A30" stroke="#22C55E" strokeWidth="1.4" />
          <path d={`M25,${y} l2.6,2.6 l5,-6`} stroke="#22C55E" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <animate attributeName="opacity" values="0;0;1;1" dur="2.8s" begin={`${i * 0.3}s`} repeatCount="indefinite" />
          </path>
          <rect x="44" y={y - 2.5} height="4.5" rx="2.2" fill="#475569">
            <animate attributeName="width" values="0;82;82" dur="2.8s" begin={`${i * 0.3}s`} repeatCount="indefinite" />
          </rect>
        </g>
      ))}
      <circle cx="188" cy="40" r="22" stroke="#1B3A5C" strokeWidth="5" fill="none" />
      <circle cx="188" cy="40" r="22" stroke="#22C55E" strokeWidth="5" fill="none" strokeLinecap="round" strokeDasharray="138.2" transform="rotate(-90 188 40)">
        <animate attributeName="stroke-dashoffset" values="138.2;34;34" dur="2.8s" repeatCount="indefinite" />
      </circle>
      <text x="188" y="43.5" textAnchor="middle" fill="#22C55E" fontSize="10.5" fontWeight="700" fontFamily="monospace">DPDP</text>
    </svg>
  );
}
