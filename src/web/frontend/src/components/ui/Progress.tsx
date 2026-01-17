import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  variant?: 'default' | 'gradient';
  size?: 'sm' | 'md' | 'lg';
}

export default function Progress({
  value,
  max = 100,
  className,
  showLabel = false,
  variant = 'default',
  size = 'md',
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={cn('w-full', className)}>
      <div className={cn('w-full bg-dark-700 rounded-full overflow-hidden', sizes[size])}>
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            variant === 'gradient'
              ? 'bg-gradient-to-r from-primary-500 to-accent-500'
              : 'bg-primary-500'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="mt-1 text-xs text-dark-400 text-right">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
}
