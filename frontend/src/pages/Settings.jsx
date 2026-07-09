import { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon, Save, Building, Mail, HardDrive,
  FileText, Upload, Link, CheckCircle, XCircle, RefreshCw,
  ExternalLink, AlertCircle, Database
} from 'lucide-react'
import toast from 'react-hot-toast'
import { defaultInterviewTemplate, defaultOfferTemplate, defaultCertificateTemplate } from '../utils/defaultTemplates'

const BACKEND_URL = '' // Same origin via Vite proxy

// ─── Google Sheet URL Card (prominent, top-level) ─────────────────────────────
function SheetUrlCard({ form, setForm, onTest }) {
  const [testing, setTesting] = useState({})
  const [testResults, setTestResults] = useState({})

  const handleTest = async (field, url) => {
    if (!url) return toast.error('Please enter a URL first')
    setTesting(t => ({ ...t, [field]: true }))
    try {
      const res = await fetch('/api/settings/test-sheet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const data = await res.json()
      if (res.ok && data.success) {
        setTestResults(r => ({ ...r, [field]: { ok: true, info: `✓ "${data.sheet_name}" — ${data.row_count} rows, columns: ${data.columns?.slice(0, 4).join(', ')}` } }))
        toast.success(`Connected to "${data.sheet_name}"`)
      } else {
        setTestResults(r => ({ ...r, [field]: { ok: false, info: data.detail || 'Connection failed' } }))
        toast.error('Connection failed — check URL and sheet permissions')
      }
    } catch {
      setTestResults(r => ({ ...r, [field]: { ok: false, info: 'Backend not running' } }))
      toast.error('Backend not reachable. Start the FastAPI server.')
    }
    setTesting(t => ({ ...t, [field]: false }))
  }

  const fields = [
    {
      key:   'registration_sheet_url',
      label: 'Registration Sheet URL',
      desc:  'Main sheet where candidates register. Used by Shortlisting, Candidates, Dashboard.',
      badge: 'Primary',
      badgeColor: 'bg-primary-500/20 text-primary-300 border-primary-500/30',
      required: true,
    },
    {
      key:   'interview_response_sheet_url',
      label: 'Interview Response Sheet URL',
      desc:  'Form response sheet where candidates confirm interview availability.',
      badge: 'For Hiring',
      badgeColor: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
      required: false,
    },
    {
      key:   'offer_details_sheet_url',
      label: 'Offer Details Sheet URL',
      desc:  'Sheet where hired candidates submit bank details, PAN, address for offer generation.',
      badge: 'For Offers',
      badgeColor: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      required: false,
    },
  ]

  return (
    <div className="space-y-4">
      {/* Header banner */}
      <div className="p-4 rounded-xl border border-primary-500/20 bg-primary-500/5 flex items-start gap-3">
        <Database size={18} className="text-primary-400 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-white">Google Sheet Integration</p>
          <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
            Paste your Google Sheet URLs below. The portal will read and write candidate data directly to these sheets.
            Make sure your <span className="text-primary-300 font-medium">service_account.json</span> has editor access to each sheet.
          </p>
        </div>
      </div>

      {fields.map(f => (
        <div key={f.key} className="glass-card p-4 space-y-3">
          {/* Label row */}
          <div className="flex items-center gap-2 flex-wrap">
            <label className="text-sm font-semibold text-white">{f.label}</label>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${f.badgeColor}`}>
              {f.badge}
            </span>
            {f.required && <span className="text-xs text-red-400">* required</span>}
          </div>
          <p className="text-xs text-slate-500">{f.desc}</p>

          {/* URL Input + Test button */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Link size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="url"
                value={form[f.key] || ''}
                onChange={e => setForm(frm => ({ ...frm, [f.key]: e.target.value }))}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                className="input-field pl-8 text-xs font-mono"
              />
            </div>
            <button
              onClick={() => handleTest(f.key, form[f.key])}
              disabled={testing[f.key]}
              className="btn-secondary text-xs px-3 flex-shrink-0"
            >
              {testing[f.key]
                ? <RefreshCw size={12} className="animate-spin" />
                : <CheckCircle size={12} />
              }
              Test
            </button>
            {form[f.key] && (
              <a
                href={form[f.key]}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost text-xs px-3 flex-shrink-0"
                title="Open sheet"
              >
                <ExternalLink size={12} />
              </a>
            )}
          </div>

          {/* Test result */}
          {testResults[f.key] && (
            <div className={`flex items-start gap-2 text-xs px-3 py-2 rounded-lg ${testResults[f.key].ok ? 'bg-green-500/10 text-green-300 border border-green-500/20' : 'bg-red-500/10 text-red-300 border border-red-500/20'}`}>
              {testResults[f.key].ok
                ? <CheckCircle size={12} className="flex-shrink-0 mt-0.5" />
                : <XCircle size={12} className="flex-shrink-0 mt-0.5" />
              }
              <span>{testResults[f.key].info}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Sections nav ──────────────────────────────────────────────────────────────
const SECTIONS = [
  { id: 'sheets',    label: 'Google Sheets', icon: Database },
  { id: 'company',  label: 'Company',        icon: Building },
  { id: 'smtp',     label: 'SMTP / Email',   icon: Mail },
  { id: 'storage',  label: 'Drive Storage',  icon: HardDrive },
  { id: 'templates',label: 'Templates',      icon: FileText },
]

export default function Settings() {
  const [activeSection, setActiveSection] = useState('sheets')
  const [form, setForm] = useState({
    // Sheets
    registration_sheet_url:        '',
    interview_response_sheet_url:  '',
    offer_details_sheet_url:       '',
    // Company
    company_name:    'SwipeGen Technologies',
    website_url:     '',
    // SMTP
    sender_email:    '',
    sender_password: '',
    smtp_port:       '587',
    email_signature: 'Regards,\nHR Team\nSwipeGen Technologies',
    // Storage
    certificates_drive_folder_id:  '',
    offer_letters_drive_folder_id: '',
    // Templates
    offer_template: 'Default Offer Template',
    cert_template:  'Default Certificate Template',
    interview_email_template: '',
    offer_email_template: '',
    certificate_email_template: '',
  })
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [backendStatus, setBackendStatus] = useState(null)

  // Load settings from backend on mount
  useEffect(() => {
    loadSettings()
    checkBackend()
  }, [])

  const checkBackend = async () => {
    try {
      const res = await fetch('/api/health')
      const data = await res.json()
      setBackendStatus(data)
    } catch {
      setBackendStatus(null)
    }
  }

  const loadSettings = async () => {
    try {
      const res = await fetch('/api/settings')
      if (res.ok) {
        const data = await res.json()
        setForm(f => ({
          ...f,
          registration_sheet_url:        data.registration_sheet_url        || '',
          interview_response_sheet_url:  data.interview_response_sheet_url  || '',
          offer_details_sheet_url:       data.offer_details_sheet_url       || '',
          company_name:    data.company_name    || 'SwipeGen Technologies',
          website_url:     data.website_url     || '',
          sender_email:    data.sender_email    || '',
          sender_password: data.sender_password || '',
          smtp_port:       data.smtp_port       || '587',
          certificates_drive_folder_id:  data.certificates_drive_folder_id  || '',
          offer_letters_drive_folder_id: data.offer_letters_drive_folder_id || '',
        }))
      }
      
      const resTpl = await fetch('/api/settings/templates')
      if (resTpl.ok) {
        const tplData = await resTpl.json()
        setForm(f => ({
          ...f,
          interview_email_template: tplData.interview || '',
          offer_email_template: tplData.offer || '',
          certificate_email_template: tplData.certificate || '',
        }))
      }
    } catch {
      // Backend not running — use localStorage fallback
      const saved = localStorage.getItem('hr_settings')
      if (saved) setForm(f => ({ ...f, ...JSON.parse(saved) }))
    }
    setLoading(false)
  }

  const save = async () => {
    setSaving(true)
    try {
      const res = await fetch('/api/settings', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          registration_sheet_url:        form.registration_sheet_url,
          interview_response_sheet_url:  form.interview_response_sheet_url,
          offer_details_sheet_url:       form.offer_details_sheet_url,
          sender_email:    form.sender_email,
          sender_password: form.sender_password !== '••••••••' ? form.sender_password : undefined,
          smtp_port:       form.smtp_port,
          company_name:    form.company_name,
          website_url:     form.website_url,
          certificates_drive_folder_id:  form.certificates_drive_folder_id,
          offer_letters_drive_folder_id: form.offer_letters_drive_folder_id,
        }),
      })
      if (res.ok) {
        // Also save templates
        const resTpl = await fetch('/api/settings/templates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            interview: form.interview_email_template,
            offer: form.offer_email_template,
            certificate: form.certificate_email_template
          })
        })
        if (resTpl.ok) {
          toast.success('✅ Settings and templates saved')
        } else {
          toast.success('✅ Settings saved (Templates failed)')
        }
      } else {
        throw new Error('Save failed')
      }
    } catch {
      // Fallback to localStorage
      localStorage.setItem('hr_settings', JSON.stringify(form))
      toast.success('✅ Settings saved locally (start backend to persist to .env)')
    }
    setSaving(false)
    checkBackend()
  }

  const set = field => e => setForm(f => ({ ...f, [field]: e.target.value }))

  if (loading) return (
    <div className="flex items-center justify-center h-40 text-slate-400">Loading settings...</div>
  )

  return (
    <div className="space-y-5 animate-fade-in max-w-4xl">
      {/* Backend status banner */}
      <div className={`p-3 rounded-xl border flex items-center gap-3 text-sm ${backendStatus ? 'bg-green-500/5 border-green-500/20' : 'bg-yellow-500/5 border-yellow-500/20'}`}>
        {backendStatus ? (
          <>
            <CheckCircle size={15} className="text-green-400 flex-shrink-0" />
            <span className="text-green-300 font-medium">Backend connected</span>
            <span className="text-slate-500 text-xs ml-2">
              Sheet: {backendStatus.sheet_configured ? '✓' : '✗'} · 
              SMTP: {backendStatus.smtp_configured ? '✓' : '✗'} · 
              Service Account: {backendStatus.sa_file_exists ? '✓' : '✗'}
            </span>
          </>
        ) : (
          <>
            <AlertCircle size={15} className="text-yellow-400 flex-shrink-0" />
            <span className="text-yellow-300 font-medium">Backend not running</span>
            <span className="text-slate-500 text-xs ml-2">
              Run: <code className="text-yellow-300 font-mono">uvicorn main:app --reload --port 8000</code> in the project root
            </span>
          </>
        )}
      </div>

      <div className="flex gap-5">
        {/* Section nav */}
        <div className="w-44 flex-shrink-0 space-y-1">
          {SECTIONS.map(s => (
            <button key={s.id} onClick={() => setActiveSection(s.id)}
              className={`sidebar-item w-full ${activeSection === s.id ? 'active' : ''}`}>
              <s.icon size={16} className="flex-shrink-0" />
              <span>{s.label}</span>
              {s.id === 'sheets' && !form.registration_sheet_url && (
                <span className="ml-auto w-2 h-2 rounded-full bg-red-400 flex-shrink-0" />
              )}
            </button>
          ))}
        </div>

        {/* Section content */}
        <div className="flex-1 space-y-4">
          {/* ── Google Sheets ── */}
          {activeSection === 'sheets' && (
            <SheetUrlCard form={form} setForm={setForm} />
          )}

          {/* ── Company ── */}
          {activeSection === 'company' && (
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Building size={16} className="text-primary-400" /> Company Settings
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {[
                  ['company_name', 'Company Name', 'SwipeGen Technologies'],
                  ['website_url',  'Website URL',  'https://swipegen.com'],
                ].map(([field, label, placeholder]) => (
                  <div key={field}>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">{label}</label>
                    <input value={form[field]} onChange={set(field)} placeholder={placeholder} className="input-field" />
                  </div>
                ))}
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-2">Company Logo</label>
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-xl">
                    {form.company_name?.slice(0, 2).toUpperCase() || 'SG'}
                  </div>
                  <button className="btn-secondary text-xs gap-2"><Upload size={13} /> Upload Logo</button>
                </div>
              </div>
            </div>
          )}

          {/* ── SMTP ── */}
          {activeSection === 'smtp' && (
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Mail size={16} className="text-primary-400" /> SMTP / Email Configuration
              </h2>
              <div className="p-3 rounded-xl bg-primary-500/5 border border-primary-500/15 text-xs text-slate-400">
                Used for sending interview invites, offer letters, and certificates automatically.
                For Gmail, use an <span className="text-primary-300">App Password</span> (not your account password).
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  ['sender_email',    'Sender Email',  'email@gmail.com',  'email'],
                  ['sender_password', 'App Password',  '•••••••••••••••',  'password'],
                  ['smtp_port',       'SMTP Port',     '587',               'text'],
                ].map(([field, label, placeholder, type]) => (
                  <div key={field} className={field === 'sender_email' ? 'col-span-2' : ''}>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">{label}</label>
                    <input value={form[field]} onChange={set(field)} type={type}
                      placeholder={placeholder} className="input-field" />
                  </div>
                ))}
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email Signature</label>
                <textarea value={form.email_signature} onChange={set('email_signature')}
                  rows={4} className="input-field resize-none" />
              </div>
            </div>
          )}

          {/* ── Storage ── */}
          {activeSection === 'storage' && (
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <HardDrive size={16} className="text-primary-400" /> Google Drive Storage
              </h2>
              <p className="text-xs text-slate-500">Paste the folder IDs from your Google Drive URL. Generated PDFs will be saved here.</p>
              {[
                ['certificates_drive_folder_id',  'Certificates Folder ID', '1xn__RMhCoatZ-rMCERa...'],
                ['offer_letters_drive_folder_id', 'Offer Letters Folder ID','1OIBZ769PloyYYUME7wU...'],
              ].map(([field, label, placeholder]) => (
                <div key={field}>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">{label}</label>
                  <div className="flex gap-2">
                    <input value={form[field]} onChange={set(field)} placeholder={placeholder}
                      className="input-field flex-1 font-mono text-xs" />
                    {form[field] && (
                      <a href={`https://drive.google.com/drive/folders/${form[field]}`}
                        target="_blank" rel="noopener noreferrer" className="btn-ghost px-3">
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}


          {/* ── Templates ── */}
          {activeSection === 'templates' && (
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <FileText size={16} className="text-primary-400" /> Document Templates
              </h2>
              {[
                ['offer_template', 'Offer Letter Template'],
                ['cert_template',  'Certificate Template'],
              ].map(([field, label]) => (
                <div key={field}>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">{label}</label>
                  <div className="flex items-center gap-3">
                    <input value={form[field]} onChange={set(field)} className="input-field flex-1" />
                    <button className="btn-secondary text-xs flex-shrink-0"><Upload size={13} /> Upload</button>
                  </div>
                </div>
              ))}

              {/* Email Templates */}
              <div className="pt-4 border-t border-slate-700/50 space-y-4">
                <h3 className="text-sm font-semibold text-white">Email HTML Templates</h3>
                {[
                  ['interview_email_template', 'Interview Invite Email (Placeholders: {name}, {form_url})', defaultInterviewTemplate],
                  ['offer_email_template', 'Offer Letter Email (Placeholders: {name}, {role}, {start_date}, {expiry_date})', defaultOfferTemplate],
                  ['certificate_email_template', 'Completion Certificate Email (Placeholders: {name})', defaultCertificateTemplate],
                ].map(([field, label, defaultTemplate]) => (
                  <div key={field}>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-semibold text-slate-400">{label}</label>
                      <button 
                        onClick={() => setForm(f => ({ ...f, [field]: defaultTemplate }))}
                        className="text-[10px] text-primary-400 hover:text-primary-300 px-2 py-0.5 rounded border border-primary-500/30 bg-primary-500/10"
                      >
                        Load Default
                      </button>
                    </div>
                    <textarea 
                      value={form[field]} 
                      onChange={set(field)} 
                      rows={6}
                      className="input-field w-full font-mono text-xs whitespace-pre" 
                      placeholder="<html>...</html>"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Save button — always visible */}
          <div className="flex items-center gap-3">
            <button onClick={save} disabled={saving} className="btn-primary">
              {saving ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Saving...
                </span>
              ) : (
                <><Save size={15} /> Save Settings</>
              )}
            </button>
            <button onClick={loadSettings} className="btn-ghost text-xs">
              <RefreshCw size={13} /> Reload from backend
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
