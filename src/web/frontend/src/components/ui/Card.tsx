import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'bordered';
  hover?: boolean;
  glow?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', hover, glow, children, ...props }, ref) => {
    const variants = {
      default: 'bg-dark-800/50 border border-dark-700',
      glass: 'bg-white/5 backdrop-blur-md border border-white/10',
      bordered: 'bg-transparent border-2 border-dark-600',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl p-6 transition-all duration-300',
          variants[variant],
          hover && 'hover:border-primary-500/50 hover:bg-dark-800/70 cursor-pointer',
          glow && 'hover:shadow-[0_0_30px_rgba(59,130,246,0.2)]',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
export default Card;
