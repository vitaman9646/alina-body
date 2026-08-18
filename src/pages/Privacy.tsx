import { Eyebrow, Section } from '../components/ui';

export default function Privacy() {
  return (
    <Section>
      <Eyebrow>Документы</Eyebrow>
      <h1 className="font-display text-[44px] leading-tight sm:text-[56px]">Политика конфиденциальности</h1>
      <div className="mt-10 max-w-2xl space-y-5 text-sm leading-relaxed text-stone">
        <p>
          Мы обрабатываем только те данные, которые нужны для входа, оплаты и доступа к программам: имя, email, сведения о заказе.
        </p>
        <p>
          Данные не продаются и не передаются третьим лицам, кроме платёжного провайдера ЮKassa и инфраструктуры, необходимой для работы сайта.
        </p>
        <p>
          Вы можете запросить удаление аккаунта, написав на почту, указанную в личном кабинете.
        </p>
        <p>
          Cookies используются для авторизации и корректной работы платформы.
        </p>
      </div>
    </Section>
  );
}
