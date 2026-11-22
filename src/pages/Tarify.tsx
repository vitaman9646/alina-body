import { Eyebrow, Section } from '../components/ui';
import Seo from '../components/Seo';

const EMAIL = 'alinabody642@gmail.com';

const TARIFFS = [
  {
    name: 'Обучающие курсы',
    price: '1 500 ₽',
    desc: 'Полный курс: пошаговые уроки, рецепты с граммовками и КБЖУ, техники, доступ к материалам.',
  },
  {
    name: 'Мини-курсы',
    price: '399 ₽',
    desc: 'Короткий интенсив по узкой теме: экспресс-программа или набор материалов.',
  },
];

export default function Tarify() {
  return (
    <Section>
      <Seo title="Тарифы — Alina Body" path="/tarify" />
      <Eyebrow>Тарифы</Eyebrow>
      <h1 className="font-display text-[40px] leading-tight sm:text-[52px]">Цены и тарифы</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-stone">
        Точная стоимость каждого продукта указана на его странице до момента оплаты. Ниже — действующие
        категории и цены.
      </p>

      <div className="mt-8 grid max-w-2xl gap-4">
        {TARIFFS.map((t) => (
          <div key={t.name} className="rounded-2xl border border-ink/8 bg-white/60 p-6">
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="font-display text-xl text-ink">{t.name}</h2>
              <span className="whitespace-nowrap font-display text-2xl text-rose">{t.price}</span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-stone">{t.desc}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 max-w-xl space-y-2 text-sm text-stone">
        <p className="text-xs text-muted">
          Оплата производится через платёжную систему Platega (СБП, криптовалюты). После оплаты доступ
          к материалам открывается автоматически.
        </p>
        <p>
          Вопросы по оплате: <a href={`mailto:${EMAIL}`} className="text-rose hover:underline">{EMAIL}</a>
        </p>
      </div>
    </Section>
  );
}
