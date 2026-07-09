import { getStatusConfig } from '../utils/helpers'

export default function StatusBadge({ status, size = 'sm' }) {
  const config = getStatusConfig(status)
  const sizeClass = size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs'
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${sizeClass} ${config.className}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5" style={{ background: config.color }} />
      {config.label}
    </span>
  )
}
