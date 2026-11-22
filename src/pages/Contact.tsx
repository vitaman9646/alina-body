import { Eyebrow, Section } from '../components/ui';
import Seo from '../components/Seo';

const EMAIL = 'alinabody642@gmail.com';
const TG = 'https://t.me/alinabodyfree';

export default function Contact() {
  return (
    <Section>
      <Seo title="Контакты — Alina Body" path="/contacts" />
      <Eyebrow>Поддержка</Eyebrow>
      <h1 className="font-display text-[40px] leading-tight sm:text-[52px]">Контакты</h1>
      <div className="mt-8 max-w-xl space-y-4 text-sm leading-relaxed text-stone">
        <p>
          По вопросам оплаты, доступа к материалам и возвратов — пишите на почту поддержки. Отвечаем
          в течение одного рабочего дня.
        </p>
        <div className="space-y-2">
          <p>
            <span className="text-muted">Почта поддержки: </span>
            <a href={`mailto:${EMAIL}`} className="text-rose hover:underline">{EMAIL}</a>
          </p>
          <p>
            <span className="text-muted">Telegram-канал: </span>
            <a href={TG} target="_blank" rel="noreferrer" className="text-rose hover:underline">
              t.me/alinabodyfree
            </a>
          </p>
        </div>
      </div>
    </Section>
  );
}
