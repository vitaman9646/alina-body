import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const links = [
  { to: '/#programs', label: 'Программы' },
  { to: '/challenge', label: 'Челлендж' },
  { to: '/course', label: 'Курс' },
  { to: '/#about', label: 'Об Алине' },
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-ink/5 bg-milk/80 backdrop-blur-xl">
      <div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5" onClick={() => setOpen(false)}>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blush">
            <span className="font-display text-[17px] italic leading-none text-[#5C4038]">A</span>
          </span>
          <span className="font-display text-[22px] tracking-[0.03em] text-ink">
            Alina <span className="italic font-normal">Body</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className="text-[13px] tracking-wide text-stone transition hover:text-ink"
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            to={user ? '/dashboard' : '/auth'}
            className="text-[13px] tracking-wide text-stone hover:text-ink"
          >
            {user ? 'Кабинет' : 'Войти'}
          </Link>
          <Link
            to="/#programs"
            className="rounded-full bg-ink px-5 py-2.5 text-[12px] font-medium tracking-wide text-cream transition hover:bg-[#2b241f]"
          >
            Выбрать программу
          </Link>
        </div>

        <button
          className="md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? 'Закрыть меню' : 'Открыть меню'}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="border-t border-ink/5 bg-milk px-5 py-6 md:hidden">
          <div className="flex flex-col gap-4">
            {links.map((l) => (
              <Link key={l.to} to={l.to} onClick={() => setOpen(false)} className="text-[15px] text-ink">
                {l.label}
              </Link>
            ))}
            <Link to={user ? '/dashboard' : '/auth'} onClick={() => setOpen(false)} className="text-[15px] text-ink">
              {user ? 'Личный кабинет' : 'Войти'}
            </Link>
            <Link
              to="/#programs"
              onClick={() => setOpen(false)}
              className="mt-2 inline-flex items-center justify-center rounded-full bg-ink px-5 py-3 text-[13px] text-cream"
            >
              Выбрать программу
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
