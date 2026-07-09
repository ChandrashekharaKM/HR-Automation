import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatDate(date) {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

export function formatDateTime(date) {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

export function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

export function getStatusConfig(status) {
  const configs = {
    applied:     { label: 'Applied',      className: 'badge-applied',     color: '#94a3b8' },
    shortlisted: { label: 'Shortlisted',  className: 'badge-shortlisted', color: '#60a5fa' },
    interview:   { label: 'Interview',    className: 'badge-interview',   color: '#c084fc' },
    accepted:    { label: 'Accepted',     className: 'badge-accepted',    color: '#2dd4bf' },
    hired:       { label: 'Hired',        className: 'badge-hired',       color: '#4ade80' },
    offer:       { label: 'Offer Sent',   className: 'badge-offer',       color: '#fbbf24' },
    completed:   { label: 'Completed',    className: 'badge-completed',   color: '#818cf8' },
    rejected:    { label: 'Rejected',     className: 'badge-rejected',    color: '#f87171' },
  }
  return configs[status?.toLowerCase()] || configs.applied
}

export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
