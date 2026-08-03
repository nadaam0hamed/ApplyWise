'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { LogOut, Menu, X } from 'lucide-react';

import { useAuth } from '@/hooks/useAuth';

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Features', href: '/features' },
    { label: 'How it Works', href: '/how-it-works' },
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
  ];

  const handleLogout = async () => {
    await logout();
    setIsOpen(false);
  };

  const handleSignIn = () => {
    router.push('/login');
  };

  const handleGetStarted = () => {
    if (user) {
      router.push('/dashboard');
    } else {
      router.push('/signup');
    }
  };

  const userName = user?.fullName ?? user?.email ?? '';

  return (
    <header className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center">
              <img
                src="/applywise-logo.png"
                alt="ApplyWise Logo"
                className="w-full h-full object-contain drop-shadow-lg"
              />
            </div>
            <div>
              <span className="font-bold text-base sm:text-lg text-foreground">
                Apply<span className="text-primary">Wise</span>
              </span>
              <p className="text-[10px] sm:text-xs text-muted-foreground hidden sm:block">Apply Smarter. Stress Less.</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 lg:gap-8">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3 lg:gap-4">
            {loading ? (
              <span className="text-sm text-muted-foreground">Loading...</span>
            ) : user ? (
              <>
                <span className="text-sm text-muted-foreground hidden lg:block">{userName}</span>
                <button
                  onClick={handleLogout}
                  className="px-4 lg:px-6 py-2 text-sm font-medium text-foreground border border-primary/30 hover:border-primary rounded-lg transition-colors flex items-center gap-2"
                >
                  <LogOut size={16} />
                  <span className="hidden lg:inline">Logout</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleSignIn}
                  className="px-4 lg:px-6 py-2 text-sm font-medium text-foreground border border-primary/30 hover:border-primary rounded-lg transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={handleGetStarted}
                  className="px-4 lg:px-6 py-2 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-medium hover:shadow-lg hover:shadow-primary/20 transition-all"
                >
                  Get Started
                </button>
              </>
            )}
          </div>

          <button
            className="md:hidden p-2 hover:bg-muted rounded-lg transition-colors touch-manipulation"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle menu"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {isOpen && (
          <div className="md:hidden py-4 border-t border-border animate-in slide-in-from-top duration-200">
            <nav className="flex flex-col gap-4">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="text-base font-medium text-muted-foreground hover:text-foreground transition-colors py-2 touch-manipulation"
                  onClick={() => setIsOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <div className="flex flex-col gap-3 pt-4 border-t border-border/50">
                {loading ? (
                  <p className="text-sm text-muted-foreground">Loading...</p>
                ) : user ? (
                  <>
                    <p className="text-sm text-muted-foreground">Welcome, {userName}</p>
                    <button
                      onClick={handleLogout}
                      className="px-4 py-3 text-sm font-medium text-foreground border border-border rounded-lg flex items-center justify-center gap-2 touch-manipulation"
                    >
                      <LogOut size={16} />
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        handleSignIn();
                        setIsOpen(false);
                      }}
                      className="px-4 py-3 text-sm font-medium text-foreground hover:text-primary transition-colors border border-border rounded-lg touch-manipulation"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => {
                        handleGetStarted();
                        setIsOpen(false);
                      }}
                      className="px-4 py-3 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-medium touch-manipulation"
                    >
                      Get Started
                    </button>
                  </>
                )}
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
