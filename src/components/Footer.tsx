import { Link } from 'react-router-dom';

const TG = 'https://t.me/alinabodyfree';

export default function Footer() {
  return (
    <footer className="border-t border-ink/8 bg-[#F3EBE3] px-5 py-16 sm:px-8">
      <div className="mx-auto grid max-w-6xl gap-12 md:grid-cols-3">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blush">
              <span className="font-display text-[17px] italic text-[#5C4038]">A</span>
            </span>
            <span className="font-display text-[22px] text-ink">
              Alina <span className="italic">Body</span>
            </span>
          </div>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-muted">
            Женское благополучие: тренировки, питание и забота о себе — без давления и жёстких ограничений.
          </p>
        </div>

        <div>
          <p className="mb-4 text-[11px] uppercase tracking-[0.22em] text-rose">Алина</p>
          <div className="flex flex-col gap-2.5 text-sm text-stone">
            <Link to="/#about" className="hover:text-ink">Об Алине</Link>
            <Link to="/blog" className="hover:text-ink">Блог</Link>
            <a href={TG} target="_blank" rel="noreferrer" className="hover:text-ink">Telegram-канал</a>
          </div>
        </div>

        <div>
          <p className="mb-4 text-[11px] uppercase tracking-[0.22em] text-rose">Документы</p>
          <div className="flex flex-col gap-2.5 text-sm text-stone">
            <Link to="/terms" className="hover:text-ink">Оферта</Link>
            <Link to="/privacy" className="hover:text-ink">Конфиденциальность</Link>
          </div>
        </div>
      </div>
      <div className="mx-auto mt-14 max-w-6xl border-t border-ink/8 pt-6 text-xs text-muted">
        © {new Date().getFullYear()} Alina Body. Все права защищены.
      </div>
    </footer>
  );
}
