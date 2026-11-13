export default function Terms() {
  return (
    <div className="min-h-screen bg-milk px-5 py-16 text-ink sm:px-8">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-3xl">Условия использования</h1>
        <div className="mt-6 space-y-4 leading-relaxed text-stone">
          <p>
            Материалы Alina Body — программы тренировок, рецепты и меню — предоставляются
            в информационных целях и не являются медицинской консультацией. Перед началом
            тренировок или изменением питания при наличии противопоказаний проконсультируйтесь
            со специалистом.
          </p>
          <p>
            Приобретая доступ к курсу или подписке, вы получаете право личного использования
            материалов. Копирование, перепродажа и распространение материалов без согласия
            автора запрещены.
          </p>
          <p>
            Возврат средств: если доступ не был активирован или материал не соответствует
            описанию — напишите в канал, вопрос решается индивидуально.
          </p>
          <p>
            Все вопросы — в Telegram-канале:{' '}
            <a href="https://t.me/alinabodyfree" className="text-rose hover:underline">
              t.me/alinabodyfree
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
