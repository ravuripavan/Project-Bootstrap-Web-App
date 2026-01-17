import { Bell, User } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-16 border-b border-dark-700 bg-dark-900/50 flex items-center justify-between px-6">
      <div />

      <div className="flex items-center gap-4">
        <button className="p-2 rounded-lg text-dark-400 hover:text-dark-200 hover:bg-dark-800 transition-colors">
          <Bell className="w-5 h-5" />
        </button>
        <button className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </button>
      </div>
    </header>
  );
}
