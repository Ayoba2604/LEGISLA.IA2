export function normalizeProfileName(name = '') {
  return String(name).replace(/\s+/g, ' ').trim()
}

export function getUserInitials(name = '') {
  const parts = normalizeProfileName(name).split(' ').filter(Boolean).slice(0, 2)
  if (!parts.length) return 'IA'
  return parts.map((part) => part[0].toUpperCase()).join('')
}
