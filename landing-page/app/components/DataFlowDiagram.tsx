import { FileText, Cpu, BarChart3, ShieldCheck, Lock, X, Check } from "lucide-react";

/**
 * Animated data-flow diagram for the "how the local agent works" section.
 * Visualises the privacy boundary: raw files stay on-device, only metadata
 * crosses to the cloud dashboard.
 */
export default function DataFlowDiagram() {
  return (
    <div className="dataflow" data-animate>
      {/* LOCAL ZONE */}
      <div className="df-zone df-local">
        <span className="df-tag df-tag-local">Your Device</span>
        <div className="df-files">
          <span className="df-chip"><FileText size={14} /> Docs</span>
          <span className="df-chip"><FileText size={14} /> Configs</span>
          <span className="df-chip"><FileText size={14} /> Policies</span>
        </div>
        <div className="df-node">
          <span className="df-node-icon"><Cpu size={18} /></span>
          <div>
            <strong>Local Agent</strong>
            <em>Scans · applies rulepacks · generates findings</em>
          </div>
        </div>
        <span className="df-foot df-foot-ok"><Lock size={12} /> Raw data never leaves this device</span>
      </div>

      {/* BRIDGE / TRUST BOUNDARY */}
      <div className="df-bridge">
        <span className="df-blocked"><X size={13} /> Raw files blocked</span>
        <div className="df-wire">
          <span className="df-packet" />
        </div>
        <span className="df-allowed"><Check size={13} /> Metadata only · TLS + JWT</span>
      </div>

      {/* CLOUD ZONE */}
      <div className="df-zone df-cloud">
        <span className="df-tag df-tag-cloud">Cloud Dashboard</span>
        <div className="df-node">
          <span className="df-node-icon df-node-icon-cloud"><BarChart3 size={18} /></span>
          <div>
            <strong>Findings &amp; audit trail</strong>
            <em>No raw files · audit-ready exports</em>
          </div>
        </div>
        <span className="df-foot df-foot-cloud"><ShieldCheck size={12} /> Inspect anywhere, securely</span>
      </div>
    </div>
  );
}
