import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-ink/8 bg-[#F3EBE3] px-5 py-16 sm:px-8">
      <div className="mx-auto grid max-w-6xl gap-12 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blush">
              <span className="font-display text-[17px] italic text-[#5C4038]">A</span>
            </span>
            <span className="font-display text-[22px] text-ink">
              Alina <span className="italic">Body</span>
            </span>
          </div>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-muted">
            Онлайн-платформа домашнего фитнеса. Мягкая сила, осанка и устойчивый тон — без крика и жёстких ограничений.
          </p>
        </div>

        <div>
          <p className="mb-4 text-[11px] uppercase tracking-[0.22em] text-rose">Платформа</p>
          <div className="flex flex-col gap-2.5 text-sm text-stone">
            <Link to="/challenge" className="hover:text-ink">Челлендж 21 день</Link>
            <Link to="/course" className="hover:text-ink">Курс 8 недель</Link>
            <Link to="/dashboard" className="hover:text-ink">Личный кабинет</Link>
            <Link to="/auth" className="hover:text-ink">Вход</Link>
          </div>
        </div>

        <div>
          <p className="mb-4 text-[11px] uppercase tracking-[0.22em] text-rose">Документы</p>
          <div className="flex flex-col gap-2.5 text-sm text-stone">
            <Link to="/terms" className="hover:text-ink">Оферта</Link>
            <Link to="/privacy" className="hover:text-ink">Конфиденциальность</Link>
          </div>
          <p className="mt-6 text-xs leading-relaxed text-muted">
            Видео доступны только онлайн. PDF можно скачать после оплаты.
          </p>
        </div>
      </div>
      <div className="mx-auto mt-14 max-w-6xl border-t border-ink/8 pt-6 text-xs text-muted">
        © {new Date().getFullYear()} Alina Body. Все права защищены.
      </div>
    </footer>
  );
}
