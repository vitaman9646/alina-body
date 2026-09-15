import { Link } from 'react-router-dom';
import { ArrowRight, Check } from 'lucide-react';
import { ButtonLink, Eyebrow, FadeIn, Section } from '../components/ui';
import { formatPrice } from '../lib/api';

// Тип темы — одна тема тела/цели = одна пара «трипваер → мини-курс»
type Theme = {
  id: string;
  title: string;
  voiceLine: string;
  tripwire: {
    title: string;
    days: number;
    minutesPerDay: number;
    price: number;
    slug: string;
    image: string;
  };
  course: {
    title: string;
    days: number;
    price: number;
    slug: string;
    image: string;
  };
};

const themes: Theme[] = [
  {
    id: 'glutes-legs',
    title: 'Ягодицы и ноги',
    voiceLine:
      'Работаем на нейромышечную связь, а не на износ — мягкая активация вместо ударных нагрузок.',
    tripwire: {
      title: '3 дня активации',
      days: 3,
      minutesPerDay: 15,
      price: 399,
      slug: 'glutes-legs-tripwire',
      image: '/images/tonus/glutes-tripwire.jpg',
    },
    course: {
      title: '7 дней: сильные ноги и упругие ягодицы',
      days: 7,
      price: 1490,
      slug: 'glutes-legs-course',
      image: '/images/tonus/glutes-course.jpg',
    },
  },
];

function ThemeSection({ theme, index }: { theme: Theme; index: number }) {
  return (
    <FadeIn delay={index * 0.05}>
      <div className="rounded-[36px] border border-ink/6 bg-white/60 p-6 md:p-10">
        <div className="max-w-xl">
          <Eyebrow>{theme.title}</Eyebrow>
          <p className="font-display text-[22px] italic leading-snug text-ink">
            «{theme.voiceLine}»
          </p>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-[1fr_auto_1.15fr] md:items-stretch">
          <Link
            to={`/tonus-doma/${theme.tripwire.slug}`}
            className="group overflow-hidden rounded-[28px] border border-sand bg-milk transition-colors hover:border-clay"
          >
            <img
              src={theme.tripwire.image}
              alt={theme.tripwire.title}
              className="h-48 w-full object-cover"
            />
            <div className="p-6">
              <p className="text-[11px] uppercase tracking-[0.22em] text-rose">Попробовать</p>
              <h3 className="mt-2 font-display text-[26px] leading-tight">{theme.tripwire.title}</h3>
              <p className="mt-2 text-sm text-stone">
                {theme.tripwire.days} дня · {theme.tripwire.minutesPerDay} минут в день
              </p>
              <p className="mt-4 font-display text-[28px]">{formatPrice(theme.tripwire.price)}</p>
            </div>
          </Link>

          <div className="hidden items-center justify-center md:flex">
            <div className="h-px w-10 bg-gradient-to-r from-sand to-clay" />
          </div>
          <div className="flex items-center justify-center md:hidden">
            <div className="h-10 w-px bg-gradient-to-b from-sand to-clay" />
          </div>

          <Link
            to={`/tonus-doma/${theme.course.slug}`}
            className="group overflow-hidden rounded-[28px] bg-blush shadow-[0_20px_50px_-32px_rgba(58,49,44,0.4)] transition-transform hover:-translate-y-0.5"
          >
            <img
              src={theme.course.image}
              alt={theme.course.title}
              className="h-48 w-full object-cover"
            />
            <div className="p-6">
              <p className="text-[11px] uppercase tracking-[0.22em] text-stone">Продолжить</p>
              <h3 className="mt-2 font-display text-[26px] leading-tight">{theme.course.title}</h3>
              <p className="mt-2 text-sm text-stone">Полная программа зоны · {theme.course.days} дней</p>
              <div className="mt-4 flex items-center justify-between">
                <p className="font-display text-[28px]">{formatPrice(theme.course.price)}</p>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-moss px-4 py-2 text-[13px] font-medium text-cream">
                  Открыть <ArrowRight size={14} />
                </span>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </FadeIn>
  );
}

export default function TonusDoma() {
  return (
    <div>
      <Section className="pt-16 pb-10">
        <FadeIn>
          <Eyebrow>Тонус дома</Eyebrow>
          <h1 className="max-w-2xl font-display text-[44px] leading-[1.05] sm:text-[58px]">
            Короткие программы <span className="italic">под свою цель</span>
          </h1>
          <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-stone">
            Начните с малого шага — 3 дня, 15 минут — и продолжайте, когда почувствуете,
            что готовы идти глубже.
          </p>
        </FadeIn>
      </Section>

      <Section className="space-y-8 pt-0">
        {themes.map((theme, i) => (
          <ThemeSection key={theme.id} theme={theme} index={i} />
        ))}
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <div className="mx-auto max-w-lg text-center">
          <Eyebrow>Готовы больше?</Eyebrow>
          <h2 className="font-display text-[32px] leading-tight sm:text-[38px]">
            Если захотите собрать всё <span className="italic">в единую систему</span>
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-stone">
            Оставьте почту — расскажем, когда будет готово, и первыми покажем новые темы.
          </p>
          <form className="mt-7 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <input
              type="email"
              required
              placeholder="Ваша почта"
              className="rounded-full border border-ink/15 bg-white px-6 py-3.5 text-sm text-ink outline-none focus:border-clay sm:w-72"
            />
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-1.5 rounded-full bg-ink px-7 py-3.5 text-[13px] font-medium text-cream transition-colors hover:bg-[#2b241f]"
            >
              <Check size={14} /> Подписаться
            </button>
          </form>
        </div>
      </Section>
    </div>
  );
}
