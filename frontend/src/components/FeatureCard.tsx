import { Link } from '@tanstack/react-router'
import type { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  to: string
  icon: LucideIcon
  title: string
  description: string
  colorScheme: {
    gradient: string
    iconBg: string
    iconText: string
    border: string
    shadow: string
    btnClass: string
  }
}

export default function FeatureCard({
  to,
  icon: Icon,
  title,
  description,
  colorScheme,
}: FeatureCardProps) {
  return (
    <Link
      to={to}
      className={`card bg-base-200 border-2 border-base-300 ${colorScheme.border} ${colorScheme.shadow} hover:shadow-xl transition-all duration-300 hover:-translate-y-1 relative overflow-hidden group`}
    >
      {/* Gradient Background Blob */}
      <div className={`absolute top-0 right-0 w-32 h-32 ${colorScheme.gradient} rounded-full blur-3xl opacity-20 group-hover:opacity-30 transition-opacity duration-300`} />
      
      <div className="card-body relative">
        <div className={`w-12 h-12 rounded-lg ${colorScheme.iconBg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
          <Icon className={`w-6 h-6 ${colorScheme.iconText}`} />
        </div>
        <h2 className="card-title">{title}</h2>
        <p className="text-base-content/70">{description}</p>
        <div className="card-actions justify-end mt-4">
          <button type="button" className={`btn btn-sm ${colorScheme.btnClass}`}>
            Get Started
          </button>
        </div>
      </div>
    </Link>
  )
}