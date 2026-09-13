import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldAlert, AlertTriangle, FileText, UploadCloud, 
  Building2, Landmark, CheckCircle2, XCircle, ArrowRight, Download, 
  History, DollarSign, RefreshCw, Lock, Zap, Check, ExternalLink, HelpCircle
} from 'lucide-react';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('audit'); // 'audit', 'vault', 'history', 'pricing'
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Quick Text Mode
  const [scanMode, setScanMode] = useState('file'); // 'file' or 'text'
  const [rawInvoiceText, setRawInvoiceText] = useState('');
  const [vendorHint, setVendorHint] = useState('');

  // Data states
  const [vendors, setVendors] = useState([]);
  const [auditHistory, setAuditHistory] = useState([]);
  const [newVendorForm, setNewVendorForm] = useState({
    vendor_name: '', official_email: '', trusted_bank_name: '',
    trusted_account: '', trusted_routing: '', trusted_iban: '', notes: ''
  });

  // Fetch Vendors and History on tab change
  useEffect(() => {
    if (activeTab === 'vault') fetchVendors();
    if (activeTab === 'history') fetchHistory();
  }, [activeTab]);

  const fetchVendors = async () => {
    try {
      const res = await fetch(`${API_BASE}/vendors/`);
      if (res.ok) setVendors(await res.json());
    } catch (err) {
      console.error("Failed to load vendors", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/audit/history`);
      if (res.ok) setAuditHistory(await res.json());
    } catch (err) {
      console.error("Failed to load history", err);
    }
  };

  // Upload handler
  const handleFileUpload = async (file) => {
    if (!file) return;
    setIsAuditing(true);
    setErrorMessage('');
    setAuditResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/audit/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || data.detail || 'Audit processing halted by security filters.');
      }
      setAuditResult(data);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsAuditing(false);
    }
  };

  // Text quick scan handler
  const handleTextScan = async () => {
    if (!rawInvoiceText.trim()) return;
    setIsAuditing(true);
    setErrorMessage('');
    setAuditResult(null);

    try {
      const res = await fetch(`${API_BASE}/audit/quick-scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: rawInvoiceText,
          vendor_name_hint: vendorHint || null
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || data.detail || 'Quick scan failed.');
      }
      setAuditResult(data);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsAuditing(false);
    }
  };

  // Quick Demo Invoices Loader
  const loadDemoCase = (caseType) => {
    setActiveTab('audit');
    setScanMode('text');
    if (caseType === 'clean') {
      setVendorHint('CloudScale Networks Inc.');
      setRawInvoiceText(`CloudScale Networks Inc.
100 Silicon Way, San Jose, CA 95134 | Tax ID: US-849302194
Email: billing@cloudscalenetworks.com

INVOICE #: CS-2026-9901
Date: September 01, 2026
Due Date: October 01, 2026

Enterprise Dedicated Cloud Cluster (Tier 3)  1  $10,000.00  $10,000.00
High-Bandwidth Global Transit (10Gbps)        1  $4,500.00   $4,500.00

Subtotal: $14,500.00
Tax (0%): $0.00
Total Amount Due: $14,500.00

WIRE REMITTANCE DETAILS:
Bank Name: JPMorgan Chase Bank, N.A.
Routing Number: 021000021
Account Number: 9842109482
IBAN: US64CHAS0210000219842109482`);
    } else if (caseType === 'fraud') {
      setVendorHint('CloudScale Networks Inc.');
      setRawInvoiceText(`CloudScale Networks Inc.
INVOICE #: CS-2026-9902
Date: September 10, 2026

Cloud Architecture Migration Services
Subtotal: $18,900.00
Tax: $0.00
Total Amount Due: $18,900.00

PAYMENT INSTRUCTIONS (UPDATED):
URGENT WIRE REQUIRED: OUR BANK ACCOUNT WAS RECENTLY UPDATED.
Bank Name: Offshore Swift Express Bank
Routing Number: 021000021
Account Number: 1112223334`);
    } else if (caseType === 'math') {
      setVendorHint('Apex Cyber Logistics LLC');
      setRawInvoiceText(`Apex Cyber Logistics LLC
INVOICE #: APX-8812
Subtotal: $5,000.00
Tax: $400.00
Total Amount Due: $6,800.00

WIRE REMITTANCE DETAILS:
Bank Name: Bank of America
Routing Number: 026009593
Account Number: 4439021984`);
    }
  };

  // Enroll new vendor
  const handleEnrollVendor = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/vendors/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newVendorForm)
      });
      if (res.ok) {
        alert(`Vendor "${newVendorForm.vendor_name}" enrolled successfully!`);
        setNewVendorForm({
          vendor_name: '', official_email: '', trusted_bank_name: '',
          trusted_account: '', trusted_routing: '', trusted_iban: '', notes: ''
        });
        fetchVendors();
      } else {
        const err = await res.json();
        alert(`Failed: ${err.detail || 'Could not enroll vendor'}`);
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    }
  };

  // Stripe Checkout
  const handleCheckout = async (tier) => {
    try {
      const res = await fetch(`${API_BASE}/billing/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: tier,
          success_url: window.location.origin + '/?success=true',
          cancel_url: window.location.origin + '/?cancel=true'
        })
      });
      const data = await res.json();
      if (data.checkout_url) {
        if (data.mode === 'live') {
          window.location.href = data.checkout_url;
        } else {
          alert(`Sandbox Mode Triggered for ${tier.toUpperCase()}: Subscription checkout initialized ($${data.amount_usd}/mo). Connect live Stripe keys in .env when ready.`);
        }
      }
    } catch (err) {
      alert(`Billing Error: ${err.message}`);
    }
  };

  // Helper for risk colors
  const getRiskClass = (level) => {
    if (level === 'CRITICAL_FRAUD') return 'critical';
    if (level === 'HIGH_RISK' || level === 'SUSPICIOUS') return 'suspicious';
    return 'clean';
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="header-bar">
        <div className="logo-group">
          <ShieldCheck className="logo-icon" />
          <div>
            <div className="logo-title">LEDGERGUARD AI</div>
            <div className="logo-subtitle">Financial Fraud & Wire Defense Platform</div>
          </div>
        </div>

        <nav className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <Zap size={15} /> Audit Cockpit
          </button>
          <button 
            className={`nav-tab ${activeTab === 'vault' ? 'active' : ''}`}
            onClick={() => setActiveTab('vault')}
          >
            <Landmark size={15} /> Vendor Vault
          </button>
          <button 
            className={`nav-tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <History size={15} /> Audit History
          </button>
          <button 
            className={`nav-tab ${activeTab === 'pricing' ? 'active' : ''}`}
            onClick={() => setActiveTab('pricing')}
          >
            <DollarSign size={15} /> SaaS Licensing
          </button>
        </nav>

        <div className="status-badge">
          <div className="pulsing-dot"></div>
          DEFENSES ARMED
        </div>
      </header>

      {/* Quick Demo Strip */}
      <div className="demo-strip">
        <span>⚡ Instant Scenarios:</span>
        <button className="demo-chip" onClick={() => loadDemoCase('clean')}>
          <CheckCircle2 size={13} color="#3fb950" /> Clean QuickBooks Invoice
        </button>
        <button className="demo-chip danger" onClick={() => loadDemoCase('fraud')}>
          <ShieldAlert size={13} color="#f85149" /> Wire Fraud (Altered Bank Account)
        </button>
        <button className="demo-chip" onClick={() => loadDemoCase('math')}>
          <AlertTriangle size={13} color="#d29922" /> Math Discrepancy & Hidden Fees
        </button>
      </div>

      {/* Main Tab Views */}
      {activeTab === 'audit' && (
        <main className="workspace-grid">
          {/* Left Panel: Upload & Document Ingestion */}
          <div className="glass-panel">
            <div className="panel-header">
              <div className="panel-title">
                <FileText size={18} color="#388bfd" />
                <span>Invoice Document Ingestion</span>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button 
                  className={`nav-tab ${scanMode === 'file' ? 'active' : ''}`}
                  onClick={() => setScanMode('file')}
                  style={{ padding: '4px 10px', fontSize: '11px' }}
                >
                  File Upload
                </button>
                <button 
                  className={`nav-tab ${scanMode === 'text' ? 'active' : ''}`}
                  onClick={() => setScanMode('text')}
                  style={{ padding: '4px 10px', fontSize: '11px' }}
                >
                  Quick Text / OCR
                </button>
              </div>
            </div>

            {scanMode === 'file' ? (
              <label 
                className="dropzone"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
                }}
              >
                <UploadCloud className="dropzone-icon" />
                <div>
                  <strong style={{ color: '#fff', fontSize: '15px' }}>Drop PDF Invoice Here</strong>
                  <p style={{ color: '#8b949e', fontSize: '12px', marginTop: '4px' }}>
                    Or click to browse from your device (PDF, PNG, JPG up to 10MB)
                  </p>
                </div>
                <input 
                  type="file" 
                  accept=".pdf,.png,.jpg,.jpeg" 
                  className="file-input"
                  onChange={(e) => {
                    if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                  }}
                />
                <span className="badge-tag" style={{ background: 'rgba(56, 139, 253, 0.15)', color: '#79c0ff' }}>
                  🔒 Bound Memory Sandbox Active
                </span>
              </label>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input 
                  type="text"
                  placeholder="Optional: Vendor Name (e.g. CloudScale Networks Inc.)"
                  value={vendorHint}
                  onChange={(e) => setVendorHint(e.target.value)}
                  style={{
                    background: 'rgba(8, 12, 22, 0.8)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: '13px',
                    outline: 'none'
                  }}
                />
                <textarea 
                  className="text-area"
                  placeholder="Paste invoice text, OCR scan, or email wire instructions here..."
                  value={rawInvoiceText}
                  onChange={(e) => setRawInvoiceText(e.target.value)}
                />
                <button 
                  className="btn-action btn-primary"
                  onClick={handleTextScan}
                  disabled={isAuditing || !rawInvoiceText.trim()}
                >
                  <Zap size={15} /> Execute Forensic Audit
                </button>
              </div>
            )}

            {isAuditing && (
              <div style={{ marginTop: '24px', textAlign: 'center', padding: '20px' }}>
                <RefreshCw className="pulsing-dot" style={{ width: '28px', height: '28px', margin: '0 auto 12px auto' }} />
                <div style={{ color: '#79c0ff', fontWeight: 600 }}>Executing Multi-Vector Forensic Inspection...</div>
                <div style={{ color: '#8b949e', fontSize: '12px', marginTop: '4px' }}>
                  Reconciling bank accounts • Verifying math balances • Checking metadata tamper signatures
                </div>
              </div>
            )}

            {errorMessage && (
              <div style={{ marginTop: '16px', background: 'rgba(248, 81, 73, 0.15)', border: '1px solid var(--accent-red)', color: '#ff7b72', padding: '12px 16px', borderRadius: '8px', fontSize: '13px' }}>
                <strong>Security Alert:</strong> {errorMessage}
              </div>
            )}
          </div>

          {/* Right Panel: Forensic Telemetry Cockpit */}
          <div className="glass-panel">
            <div className="panel-header">
              <div className="panel-title">
                <ShieldAlert size={18} color="#388bfd" />
                <span>Forensic Risk Telemetry</span>
              </div>
              {auditResult && (
                <button 
                  className="btn-action btn-secondary"
                  style={{ padding: '4px 12px', fontSize: '11px' }}
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(auditResult, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Audit_Report_${auditResult.audit_id.slice(0,8)}.json`;
                    a.click();
                  }}
                >
                  <Download size={12} /> Export Certificate
                </button>
              )}
            </div>

            {auditResult ? (
              <div>
                {/* Verdict Banner */}
                <div className={`verdict-banner ${getRiskClass(auditResult.risk_level)}`}>
                  {auditResult.risk_level === 'CRITICAL_FRAUD' && <ShieldAlert size={28} />}
                  {auditResult.risk_level === 'SUSPICIOUS' && <AlertTriangle size={28} />}
                  {auditResult.risk_level === 'CLEAN' && <CheckCircle2 size={28} />}
                  <div>
                    <div className="verdict-title">{auditResult.verdict}</div>
                    <div className="verdict-summary">{auditResult.ai_forensic_rationale}</div>
                  </div>
                </div>

                {/* Risk Meter Gauge */}
                <div className="risk-meter-container">
                  <div className={`score-circle ${getRiskClass(auditResult.risk_level)}`}>
                    {auditResult.risk_score}
                    <div className="score-label">RISK</div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ color: '#8b949e' }}>Audit Protocol Score:</span>
                      <strong style={{ color: '#fff' }}>{auditResult.risk_level.replace('_', ' ')}</strong>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ 
                        width: `${auditResult.risk_score}%`, 
                        height: '100%', 
                        background: auditResult.risk_score > 70 ? 'var(--accent-red)' : auditResult.risk_score > 30 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                        transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#6e7681', marginTop: '4px' }}>
                      <span>0 (Clean)</span>
                      <span>50 (Caution)</span>
                      <span>100 (Critical Fraud)</span>
                    </div>
                  </div>
                </div>

                {/* Financial & Banking Coordinates */}
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-header">
                      <Building2 size={13} /> Stated Vendor Entity
                    </div>
                    <div className="metric-value">{auditResult.vendor?.name || 'Unknown'}</div>
                    <div className="metric-sub">
                      {auditResult.vendor_known ? (
                        <span className="badge-tag clean">✓ Enrolled in Vault</span>
                      ) : (
                        <span className="badge-tag warning">⚠ Unregistered Entity</span>
                      )}
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-header">
                      <Landmark size={13} /> Banking Coordinates
                    </div>
                    <div className="metric-value">
                      {auditResult.bank_details?.account_number ? `Acc: ••••${auditResult.bank_details.account_number.slice(-4)}` : (auditResult.bank_details?.iban ? `IBAN: ${auditResult.bank_details.iban.slice(0,8)}••` : 'No Wire Data')}
                    </div>
                    <div className="metric-sub">
                      {auditResult.bank_details_matched === true && (
                        <span className="badge-tag clean">✓ Bank Matched Vault</span>
                      )}
                      {auditResult.bank_details_matched === false && (
                        <span className="badge-tag danger">🚨 CRITICAL MISMATCH</span>
                      )}
                      {auditResult.bank_details_matched === null && (
                        <span className="badge-tag" style={{ background: 'rgba(255,255,255,0.1)' }}>Unregistered</span>
                      )}
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-header">
                      <DollarSign size={13} /> Invoice Grand Total
                    </div>
                    <div className="metric-value" style={{ color: '#79c0ff' }}>
                      ${auditResult.total_amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className="metric-sub">
                      {auditResult.math_verified ? (
                        <span className="badge-tag clean">✓ Math Reconciled</span>
                      ) : (
                        <span className="badge-tag danger">⚠ Calculation Error</span>
                      )}
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-header">
                      <Lock size={13} /> Audit Identity & Performance
                    </div>
                    <div className="metric-value" style={{ fontSize: '13px' }}>
                      {auditResult.audit_id?.slice(0, 13)}...
                    </div>
                    <div className="metric-sub" style={{ color: '#8b949e' }}>
                      Processed in {auditResult.processing_time_ms}ms
                    </div>
                  </div>
                </div>

                {/* Forensic Flags Breakdown */}
                <div style={{ marginBottom: '8px', fontSize: '13px', fontWeight: 700, color: '#f0f6fc' }}>
                  Forensic Telemetry Flags ({auditResult.forensic_flags?.length || 0})
                </div>

                <div className="flags-list">
                  {auditResult.forensic_flags?.length > 0 ? (
                    auditResult.forensic_flags.map((flag, idx) => (
                      <div key={idx} className={`flag-card ${flag.severity}`}>
                        <div className="flag-title-row">
                          <span className="flag-title">{flag.title}</span>
                          <span className={`badge-tag ${flag.severity === 'CRITICAL' ? 'danger' : flag.severity === 'HIGH' ? 'warning' : 'clean'}`}>
                            {flag.severity}
                          </span>
                        </div>
                        <div className="flag-desc">{flag.description}</div>
                        <div className="flag-rec">👉 Recommendation: {flag.recommendation}</div>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '24px', color: '#8b949e', fontSize: '13px' }}>
                      ✓ Zero forensic anomalies detected. Document adheres to all integrity heuristics.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#6e7681', padding: '40px 20px', textAlign: 'center' }}>
                <ShieldCheck size={48} style={{ opacity: 0.3, marginBottom: '14px' }} />
                <h4 style={{ color: '#8b949e', marginBottom: '6px' }}>Ready for Invoice Inspection</h4>
                <p style={{ fontSize: '12px', maxWidth: '340px' }}>
                  Upload a vendor PDF on the left, paste raw text, or select one of the instant scenarios above to execute automated accounts payable defense.
                </p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* Vendor Vault Tab */}
      {activeTab === 'vault' && (
        <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <div className="glass-panel" style={{ marginBottom: '28px' }}>
            <div className="panel-header">
              <div className="panel-title">
                <Landmark size={20} color="#388bfd" />
                <span>Authorized Vendor Banking Vault</span>
              </div>
              <span className="badge-tag clean">{vendors.length} Verified Suppliers Enrolled</span>
            </div>
            <p style={{ color: '#8b949e', fontSize: '13px', marginBottom: '18px' }}>
              LedgerGuard cross-checks every incoming PDF invoice against this encrypted registry. If an invoice requests payment to any account not listed here, a <strong>CRITICAL WIRE FRAUD RED ALERT</strong> is triggered immediately.
            </p>

            <table className="vault-table">
              <thead>
                <tr>
                  <th>Vendor Entity</th>
                  <th>Official Contact</th>
                  <th>Authorized Bank</th>
                  <th>Trusted Account / IBAN</th>
                  <th>Routing #</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map((v) => (
                  <tr key={v.id}>
                    <td><strong>{v.vendor_name}</strong></td>
                    <td style={{ color: '#79c0ff' }}>{v.official_email}</td>
                    <td>{v.trusted_bank_name}</td>
                    <td style={{ fontFamily: 'monospace' }}>{v.trusted_account}</td>
                    <td style={{ fontFamily: 'monospace' }}>{v.trusted_routing || 'N/A'}</td>
                    <td><span className="badge-tag clean">✓ VERIFIED</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Enroll Form */}
          <div className="glass-panel">
            <div className="panel-header">
              <div className="panel-title">
                <Building2 size={18} color="#388bfd" />
                <span>Enroll New Trusted Supplier Profile</span>
              </div>
            </div>
            <form onSubmit={handleEnrollVendor} style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
              <input 
                type="text" required placeholder="Vendor Entity Name"
                value={newVendorForm.vendor_name}
                onChange={e => setNewVendorForm({...newVendorForm, vendor_name: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <input 
                type="email" required placeholder="Official Billing Email"
                value={newVendorForm.official_email}
                onChange={e => setNewVendorForm({...newVendorForm, official_email: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <input 
                type="text" required placeholder="Authorized Bank Name (e.g. Chase)"
                value={newVendorForm.trusted_bank_name}
                onChange={e => setNewVendorForm({...newVendorForm, trusted_bank_name: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <input 
                type="text" required placeholder="Authorized Account Number"
                value={newVendorForm.trusted_account}
                onChange={e => setNewVendorForm({...newVendorForm, trusted_account: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <input 
                type="text" placeholder="Routing Transit Number (ABA 9-digit)"
                value={newVendorForm.trusted_routing}
                onChange={e => setNewVendorForm({...newVendorForm, trusted_routing: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <input 
                type="text" placeholder="IBAN (International Wires)"
                value={newVendorForm.trusted_iban}
                onChange={e => setNewVendorForm({...newVendorForm, trusted_iban: e.target.value})}
                style={{ background: 'rgba(8,12,22,0.8)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '10px', color: '#fff' }}
              />
              <button type="submit" className="btn-action btn-primary" style={{ gridColumn: 'span 2' }}>
                <Check size={16} /> Enroll & Fortify Supplier Profile
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Audit History Tab */}
      {activeTab === 'history' && (
        <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <div className="glass-panel">
            <div className="panel-header">
              <div className="panel-title">
                <History size={20} color="#388bfd" />
                <span>Forensic Audit Trail & Chain of Custody</span>
              </div>
              <button className="btn-action btn-secondary" onClick={fetchHistory} style={{ padding: '6px 12px', fontSize: '11px' }}>
                <RefreshCw size={12} /> Refresh
              </button>
            </div>

            <table className="vault-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Timestamp</th>
                  <th>Document / Filename</th>
                  <th>Vendor</th>
                  <th>Total Claimed</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {auditHistory.length > 0 ? (
                  auditHistory.map((item) => (
                    <tr key={item.audit_id}>
                      <td style={{ fontFamily: 'monospace', color: '#8b949e' }}>{item.audit_id.slice(0,8)}</td>
                      <td style={{ fontSize: '12px', color: '#6e7681' }}>{new Date(item.created_at).toLocaleString()}</td>
                      <td>{item.filename}</td>
                      <td><strong>{item.vendor_name || 'N/A'}</strong></td>
                      <td style={{ fontFamily: 'monospace', color: '#79c0ff' }}>
                        ${item.total_amount ? item.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
                      </td>
                      <td>
                        <span className={`badge-tag ${getRiskClass(item.risk_level)}`}>
                          {item.risk_score} / 100
                        </span>
                      </td>
                      <td>
                        <span className={`badge-tag ${getRiskClass(item.risk_level)}`}>
                          {item.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', color: '#8b949e', padding: '32px' }}>
                      No audits logged yet. Upload an invoice in the Cockpit to generate forensic records.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SaaS Pricing / Licensing Tab */}
      {activeTab === 'pricing' && (
        <div style={{ padding: '36px 20px', maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '28px', color: '#fff', marginBottom: '8px' }}>
            Enterprise Commercial Licensing & Plans
          </h2>
          <p style={{ color: '#8b949e', fontSize: '14px', maxWidth: '540px', margin: '0 auto' }}>
            Deploy LedgerGuard across your Accounts Payable workflow. Catch a single altered wire before it releases, and the software pays for itself for 10 years.
          </p>

          <div className="pricing-grid">
            {/* Starter Plan */}
            <div className="price-card">
              <h3 style={{ color: '#fff' }}>Starter Auditor</h3>
              <div className="price-amount">$0<span className="price-cycle"> / free demo</span></div>
              <p style={{ color: '#8b949e', fontSize: '12px' }}>For testing and evaluating single invoices.</p>
              <div className="feature-list">
                <div className="feature-item"><Check className="feature-check" /> 10 Invoices / Month</div>
                <div className="feature-item"><Check className="feature-check" /> Math Discrepancy Checks</div>
                <div className="feature-item"><Check className="feature-check" /> Standard PDF Metadata Forensics</div>
              </div>
              <button className="btn-action btn-secondary" style={{ width: '100%' }} onClick={() => setActiveTab('audit')}>
                Current Active Tier
              </button>
            </div>

            {/* Pro Plan */}
            <div className="price-card popular">
              <div className="popular-badge">Most Popular for Businesses</div>
              <h3 style={{ color: '#fff' }}>Treasury Pro</h3>
              <div className="price-amount">$29<span className="price-cycle"> / month</span></div>
              <p style={{ color: '#8b949e', fontSize: '12px' }}>For mid-market firms & accounting practices.</p>
              <div className="feature-list">
                <div className="feature-item"><Check className="feature-check" /> <strong>Unlimited</strong> Invoice Audits</div>
                <div className="feature-item"><Check className="feature-check" /> <strong>Full Vendor Bank Vault</strong> Protection</div>
                <div className="feature-item"><Check className="feature-check" /> Dual-Engine LLM Forensic Analysis</div>
                <div className="feature-item"><Check className="feature-check" /> PDF Tampering & Splice Detection</div>
                <div className="feature-item"><Check className="feature-check" /> 1-Click Forensic Certificate Export</div>
              </div>
              <button className="btn-action btn-primary" style={{ width: '100%' }} onClick={() => handleCheckout('pro')}>
                Subscribe Pro ($29/mo)
              </button>
            </div>

            {/* Enterprise Plan */}
            <div className="price-card">
              <h3 style={{ color: '#fff' }}>Enterprise Treasury</h3>
              <div className="price-amount">$99<span className="price-cycle"> / month</span></div>
              <p style={{ color: '#8b949e', fontSize: '12px' }}>For multi-entity corporations & banks.</p>
              <div className="feature-list">
                <div className="feature-item"><Check className="feature-check" /> Everything in Treasury Pro</div>
                <div className="feature-item"><Check className="feature-check" /> 10 Team Seats & Role Permissions</div>
                <div className="feature-item"><Check className="feature-check" /> ERP / QuickBooks Webhook Integration</div>
                <div className="feature-item"><Check className="feature-check" /> Dedicated IP & Sovereign Air-Gap Option</div>
                <div className="feature-item"><Check className="feature-check" /> Custom SLA & Audit Liability Guarantee</div>
              </div>
              <button className="btn-action btn-secondary" style={{ width: '100%' }} onClick={() => handleCheckout('enterprise')}>
                Deploy Enterprise ($99/mo)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
