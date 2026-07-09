import { useEffect, useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { reportApi } from '../services/reportApi'
import { BarChart3, TrendingUp, PieChart as PieIcon, Building } from 'lucide-react'

const TABS = ['Overview', 'Pipeline', 'Colleges', 'Trends']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-bg-surface border border-border rounded-xl p-3 shadow-elevated text-xs">
      <p className="text-white font-semibold mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

export default function Reports() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('Overview')
  const [range, setRange] = useState('Monthly')

  useEffect(() => {
    reportApi.getReportsData().then(d => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-slate-400">Loading analytics...</div>
  )

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Tabs */}
      <div className="flex items-center gap-2 p-1 rounded-xl bg-white/5 border border-white/10 w-fit">
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${activeTab === t ? 'bg-primary-500 text-white' : 'text-slate-400 hover:text-white'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Range selector */}
      <div className="flex items-center gap-2">
        {['Today', 'Weekly', 'Monthly', 'Yearly'].map(r => (
          <button key={r} onClick={() => setRange(r)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
              ${range === r ? 'border-primary-500/50 bg-primary-500/10 text-primary-300' : 'border-white/10 text-slate-400 hover:text-white'}`}>
            {r}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Applications vs Hired vs Offers */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 size={15} className="text-primary-400" /> Applications Overview
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.monthly} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                <Bar dataKey="applications" name="Applications" fill="#6366f1" radius={[4,4,0,0]} />
                <Bar dataKey="hired"        name="Hired"        fill="#22c55e" radius={[4,4,0,0]} />
                <Bar dataKey="offers"       name="Offers"       fill="#f59e0b" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trend line */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp size={15} className="text-accent-400" /> Hiring Trend
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                <Line type="monotone" dataKey="applications" name="Applications" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1', r: 4 }} />
                <Line type="monotone" dataKey="hired"        name="Hired"        stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Pipeline Tab */}
      {activeTab === 'Pipeline' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <PieIcon size={15} className="text-primary-400" /> Pipeline Funnel
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={data.pipeline} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                  {data.pipeline.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="glass-card p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white mb-4">Stage Breakdown</h3>
            {data.pipeline.map(p => (
              <div key={p.name} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">{p.name}</span>
                  <span className="font-semibold" style={{ color: p.fill }}>{p.value}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${(p.value / 152) * 100}%`, background: p.fill }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Colleges Tab */}
      {activeTab === 'Colleges' && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Building size={15} className="text-primary-400" /> Top Colleges
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.colleges} layout="vertical" barCategoryGap="25%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} width={90} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Candidates" fill="#8b5cf6" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="space-y-3">
              {data.colleges.map((c, i) => (
                <div key={c.name} className="flex items-center gap-3">
                  <span className="text-xs font-bold text-slate-500 w-4">{i+1}</span>
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">{c.name}</span>
                      <span className="text-primary-400 font-semibold">{c.count}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${(c.count/55)*100}%`, background: 'linear-gradient(90deg,#6366f1,#8b5cf6)' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'Trends' && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Offer Rate vs Hire Rate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
              <Line type="monotone" dataKey="applications" name="Applications" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="hired"        name="Hired"        stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="offers"       name="Offers"       stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
