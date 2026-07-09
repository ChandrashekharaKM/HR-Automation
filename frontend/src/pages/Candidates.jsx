import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, Eye, Edit2, Trash2, ChevronUp, ChevronDown } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import StatusBadge from '../components/StatusBadge'
import Avatar from '../components/Avatar'
import { TableSkeleton } from '../components/Loader'
import AddCandidateModal from '../components/AddCandidateModal'
import toast from 'react-hot-toast'

const STATUSES = ['all','applied','shortlisted','interview','accepted','hired','offer','completed','rejected']

export default function Candidates() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortConfig, setSortConfig] = useState({ key: 'appliedDate', dir: 'desc' })
  const [showAdd, setShowAdd] = useState(false)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    const data = await candidateApi.getAll({ search, status: statusFilter })
    setCandidates(data)
    setLoading(false)
  }

  useEffect(() => { load() }, [search, statusFilter])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete ${name}?`)) return
    await candidateApi.delete(id)
    toast.success('Candidate removed')
    load()
  }

  const sorted = [...candidates].sort((a, b) => {
    const { key, dir } = sortConfig
    const va = a[key] || '', vb = b[key] || ''
    return dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
  })

  const toggleSort = (key) => {
    setSortConfig(s => ({ key, dir: s.key === key && s.dir === 'asc' ? 'desc' : 'asc' }))
  }

  const SortIcon = ({ col }) => sortConfig.key === col
    ? (sortConfig.dir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)
    : null

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by name, email, college..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>

        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="input-field pl-9 pr-4 capitalize"
            style={{ minWidth: 150 }}
          >
            {STATUSES.map(s => <option key={s} value={s} className="capitalize">{s === 'all' ? 'All Statuses' : s}</option>)}
          </select>
        </div>

        <button onClick={() => setShowAdd(true)} className="btn-primary">
          <Plus size={16} /> Add Candidate
        </button>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
          <p className="text-sm text-slate-400">
            {loading ? 'Loading...' : `${sorted.length} candidates`}
          </p>
        </div>

        {loading ? (
          <div className="p-4"><TableSkeleton rows={6} /></div>
        ) : sorted.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">🔍</p>
            <p className="text-slate-400 text-sm">No candidates found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort('college')}>
                    <span className="flex items-center gap-1">College <SortIcon col="college" /></span>
                  </th>
                  <th>Role</th>
                  <th>CGPA</th>
                  <th>Status</th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort('appliedDate')}>
                    <span className="flex items-center gap-1">Applied <SortIcon col="appliedDate" /></span>
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(c => (
                  <tr key={c.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <Avatar name={c.name} size="sm" />
                        <div>
                          <p className="text-sm font-medium text-white">{c.name}</p>
                          <p className="text-xs text-slate-500">{c.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-slate-400 text-xs">{c.college}</td>
                    <td className="text-slate-300 text-xs">{c.role}</td>
                    <td>
                      <span className={`text-sm font-semibold ${parseFloat(c.cgpa) >= 9 ? 'text-green-400' : parseFloat(c.cgpa) >= 8 ? 'text-blue-400' : 'text-slate-400'}`}>
                        {c.cgpa}
                      </span>
                    </td>
                    <td><StatusBadge status={c.status} /></td>
                    <td className="text-xs text-slate-500">{c.appliedDate?.slice(0, 10)}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button onClick={() => navigate(`/candidates/${c.id}`)} className="btn-ghost p-2 text-primary-400 hover:text-primary-300" title="View">
                          <Eye size={14} />
                        </button>
                        <button className="btn-ghost p-2 text-slate-400 hover:text-white" title="Edit">
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => handleDelete(c.id, c.name)} className="btn-ghost p-2 text-red-400 hover:text-red-300" title="Delete">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAdd && <AddCandidateModal onClose={() => setShowAdd(false)} onSave={async (data) => {
        await candidateApi.create(data)
        toast.success('Candidate added successfully!')
        setShowAdd(false)
        load()
      }} />}
    </div>
  )
}
