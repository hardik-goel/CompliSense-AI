import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'CompliSense-AI — Compliance Intelligence. Delivered.'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '1200px',
          height: '630px',
          background: '#07111F',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          justifyContent: 'center',
          padding: '80px 100px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Background accent — top right glow circle */}
        <div style={{
          position: 'absolute', top: '-120px', right: '-120px',
          width: '480px', height: '480px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
          display: 'flex',
        }}/>

        {/* Background accent — bottom left glow */}
        <div style={{
          position: 'absolute', bottom: '-80px', left: '-80px',
          width: '360px', height: '360px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34,211,238,0.08) 0%, transparent 70%)',
          display: 'flex',
        }}/>

        {/* Top left: Logo text (use text since we can't load the PNG easily in edge) */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '48px',
        }}>
          {/* Logo mark — C hexagon approximation in SVG-like div */}
          <div style={{
            width: '48px', height: '48px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #1D4ED8, #0E7490)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '22px', fontWeight: 800, color: '#fff',
          }}>
            C
          </div>
          <div style={{
            fontSize: '22px', fontWeight: 700, color: '#F1F5F9',
            letterSpacing: '-0.3px',
          }}>
            CompliSense-AI
          </div>
          <div style={{
            fontSize: '11px', color: '#64748B', marginLeft: '8px',
            border: '1px solid #1B3A5C', padding: '3px 10px', borderRadius: '4px',
            letterSpacing: '1.5px',
          }}>
            AI-NATIVE COMPLIANCE
          </div>
        </div>

        {/* Main headline */}
        <div style={{
          fontSize: '68px', fontWeight: 800, color: '#F1F5F9',
          lineHeight: 1.1, letterSpacing: '-1.5px', marginBottom: '24px',
          maxWidth: '900px',
        }}>
          Compliance Intelligence.{'\n'}Delivered.
        </div>

        {/* Sub-copy */}
        <div style={{
          fontSize: '22px', color: '#94A3B8', marginBottom: '48px',
          maxWidth: '700px', lineHeight: 1.5,
        }}>
          DPDP, AI governance, vendor reviews, and audit readiness —
          automated from one operating layer.
        </div>

        {/* Bottom row: three trust badges */}
        <div style={{ display: 'flex', gap: '16px' }}>
          {['DPDP India', 'EU AI Act', 'Audit Ready'].map(label => (
            <div key={label} style={{
              fontSize: '13px', color: '#3B82F6',
              border: '1px solid #1B3A5C', padding: '6px 16px',
              borderRadius: '6px', background: 'rgba(59,130,246,0.08)',
            }}>
              {label}
            </div>
          ))}
        </div>

        {/* Bottom right: URL watermark */}
        <div style={{
          position: 'absolute', bottom: '40px', right: '100px',
          fontSize: '14px', color: '#334155',
        }}>
          complisenseai.com
        </div>
      </div>
    ),
    { ...size }
  )
}
