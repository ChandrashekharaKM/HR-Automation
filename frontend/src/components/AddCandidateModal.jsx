import { X } from 'lucide-react'
import { useState } from 'react'

export default function AddCandidateModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    name: '', email: '', phone: '', college: '', cgpa: '', role: '', skills: ''
  })
  const [saving, setSaving] = useState(false)

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    await onSave({ ...form, skills: form.skills.split(',').map(s => s.trim()).filter(Boolean) })
    setSaving(false)
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-content">
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <h2 className="text-lg font-bold text-white">Add New Candidate</h2>
          <button onClick={onClose} className="btn-ghost p-2"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Full Name *</label>
              <input value={form.name} onChange={set('name')} required className="input-field" placeholder="Rahul Sharma" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email *</label>
              <input value={form.email} onChange={set('email')} required type="email" className="input-field" placeholder="rahul@example.com" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Phone</label>
              <input value={form.phone} onChange={set('phone')} className="input-field" placeholder="+91 98765 43210" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">College</label>
              <input value={form.college} onChange={set('college')} className="input-field" placeholder="IIT Bombay" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">CGPA</label>
              <input value={form.cgpa} onChange={set('cgpa')} className="input-field" placeholder="9.2" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Role Applied</label>
              <input value={form.role} onChange={set('role')} className="input-field" placeholder="Frontend Developer" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Skills (comma-separated)</label>
            <input value={form.skills} onChange={set('skills')} className="input-field" placeholder="React, JavaScript, TypeScript" />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
              {saving ? 'Adding...' : 'Add Candidate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
