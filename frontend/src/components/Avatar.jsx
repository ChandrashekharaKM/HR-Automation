import { getInitials } from '../utils/helpers'

export default function Avatar({ name, src, size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-base',
    xl: 'w-20 h-20 text-xl',
  }

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={`rounded-full object-cover ring-2 ring-primary-500/30 ${sizes[size]} ${className}`}
      />
    )
  }

  const initials = getInitials(name)
  const colors = [
    'from-indigo-500 to-violet-600',
    'from-blue-500 to-cyan-600',
    'from-emerald-500 to-teal-600',
    'from-orange-500 to-rose-600',
    'from-pink-500 to-fuchsia-600',
  ]
  const colorIndex = (name?.charCodeAt(0) || 0) % colors.length

  return (
    <div className={`flex items-center justify-center rounded-full bg-gradient-to-br ${colors[colorIndex]} text-white font-semibold ring-2 ring-primary-500/20 flex-shrink-0 ${sizes[size]} ${className}`}>
      {initials}
    </div>
  )
}
