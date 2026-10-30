export interface LeadMagnetCard {
  title: string;
  image: string;
}

export interface LeadMagnet {
  slug: string;
  title: string;
  tagline: string;
  description: string;
  board: string;
  tg: string;
  cards: LeadMagnetCard[];
}

const MEDIA =
  'https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/lead-magnet';
const TG = 'https://t.me/alinabodyfree';

export const leadMagnets: LeadMagnet[] = [
  {
    slug: 'tarelka',
    title: 'Гарвардская тарелка',
    tagline: 'Простой способ собрать сбалансированный приём пищи — без подсчёта калорий.',
    description: '6 карточек-шпаргалок: как разделить тарелку, сколько белка и углеводов положить, где полезные жиры и как перекусывать без срывов.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'Как собрать тарелку', image: `${MEDIA}/tarelka-1.jpg` },
      { title: 'Половина — клетчатка', image: `${MEDIA}/tarelka-2.jpg` },
      { title: 'Четверть — белки', image: `${MEDIA}/tarelka-3.jpg` },
      { title: 'Четверть — углеводы', image: `${MEDIA}/tarelka-4.jpg` },
      { title: 'Жиры — без сектора', image: `${MEDIA}/tarelka-5.jpg` },
      { title: 'Правила перекуса', image: `${MEDIA}/tarelka-6.jpg` },
    ],
  },
  {
    slug: 'dnevnik',
    title: 'Дневник питания',
    tagline: 'Как вести дневник, чтобы увидеть, что на самом деле мешает результату.',
    description: '3 карточки: зачем нужен дневник, как его вести без фанатизма и как учитывать базовую активность.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'Дневник питания — зачем', image: `${MEDIA}/dnevnik-1.jpg` },
      { title: 'Как вести дневник', image: `${MEDIA}/dnevnik-2.jpg` },
      { title: 'Базовая активность', image: `${MEDIA}/dnevnik-3.jpg` },
    ],
  },
  {
    slug: 'psihologia',
    title: 'Психология похудения',
    tagline: 'Как перестать заедать стресс и отличать голод от эмоций.',
    description: '3 карточки: голод или эмоции, 3 шага против заедания и практики успокоения без еды.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Голод или эмоции?', image: `${MEDIA}/psihologia-1.jpg` },
      { title: '3 шага против заедания', image: `${MEDIA}/psihologia-2.jpg` },
      { title: 'Практики успокоения', image: `${MEDIA}/psihologia-3.jpg` },
    ],
  },
  {
    slug: 'faq',
    title: 'FAQ похудения',
    tagline: 'Честные ответы на самые частые вопросы о похудении.',
    description: '4 карточки: почему не уходит вес, вода и разгрузочные дни, процедуры и заменители, особые случаи.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Почему не худею', image: `${MEDIA}/faq-1.jpg` },
      { title: 'Вода и разгрузочные дни', image: `${MEDIA}/faq-2.jpg` },
      { title: 'Процедуры и заменители', image: `${MEDIA}/faq-3.jpg` },
      { title: 'Если есть особенности', image: `${MEDIA}/faq-4.jpg` },
    ],
  },
  {
    slug: 'menu',
    title: 'Меню на неделю',
    tagline: 'Готовый план питания на 7 дней — без сложных рецептов.',
    description: '7 карточек — по дню на каждую: сбалансированное меню, которое легко повторить.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'День 1', image: `${MEDIA}/menu-1.jpg` },
      { title: 'День 2', image: `${MEDIA}/menu-2.jpg` },
      { title: 'День 3', image: `${MEDIA}/menu-3.jpg` },
      { title: 'День 4', image: `${MEDIA}/menu-4.jpg` },
      { title: 'День 5', image: `${MEDIA}/menu-5.jpg` },
      { title: 'День 6', image: `${MEDIA}/menu-6.jpg` },
      { title: 'День 7', image: `${MEDIA}/menu-7.jpg` },
    ],
  },
  {
    slug: 'spisok',
    title: 'Список покупок',
    tagline: 'Что купить, чтобы дома всегда было из чего приготовить полезно.',
    description: '4 карточки: что класть в корзину, принцип радуги, как читать этикетки, белок и клетчатка.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'Что класть в корзину', image: `${MEDIA}/spisok-1.jpg` },
      { title: 'Принцип радуги', image: `${MEDIA}/spisok-2.jpg` },
      { title: 'Читаем этикетки', image: `${MEDIA}/spisok-3.jpg` },
      { title: 'Белок и клетчатка', image: `${MEDIA}/spisok-4.jpg` },
    ],
  },
  {
    slug: 'supp',
    title: 'Спортпит и БАДы',
    tagline: 'Что делают аминокислоты и как принимать их с умом.',
    description: '5 карточек: ГАМК, аргинин, лизин, схема приёма и правила безопасности.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'ГАМК — спокойствие и сон', image: `${MEDIA}/supp-new-1.jpg` },
      { title: 'Аргинин — кровоток', image: `${MEDIA}/supp-new-2.jpg` },
      { title: 'Лизин — коллаген', image: `${MEDIA}/supp-new-3.jpg` },
      { title: 'Схема приёма', image: `${MEDIA}/supp-new-4.jpg` },
      { title: 'Правила приёма БАД', image: `${MEDIA}/supp-new-5.jpg` },
    ],
  },
  {
    slug: 'liver',
    title: 'Здоровье печени',
    tagline: 'Как поддержать печень питанием и привычками — без «чисток» и «детоксов».',
    description: '4 карточки: питание, образ жизни и пара растительных БАДов — честно, без обещаний.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Питание', image: `${MEDIA}/liver-new-1.jpg` },
      { title: 'Образ жизни', image: `${MEDIA}/liver-new-2.jpg` },
      { title: 'Расторопша', image: `${MEDIA}/liver-new-3.jpg` },
      { title: 'Артишок', image: `${MEDIA}/liver-new-4.jpg` },
    ],
  },
  {
    slug: 'tazovoe-dno',
    title: 'Тазовое дно',
    tagline: 'Базовые движения для контроля мышц тазового дна — мягко и без стеснения.',
    description: '4 карточки: два треугольника, перекаты таза, напряжение↔расслабление и дыхание.',
    board: 'Тренировки дома',
    tg: TG,
    cards: [
      { title: 'Два треугольника', image: `${MEDIA}/tazodno-1-dva-treugolnika.jpg` },
      { title: 'Перекаты таза', image: `${MEDIA}/tazodno-2-perekaty.jpg` },
      { title: 'Напряжение ↔ расслабление', image: `${MEDIA}/tazodno-3-napryazhenie.jpg` },
      { title: 'Дыхание', image: `${MEDIA}/tazodno-4-dyhanie.jpg` },
    ],
  },
  {
    slug: 'domashnie-trenirovki',
    title: 'Тренировки дома',
    tagline: '4 экспресс-комплекса на всё тело — без зала и инвентаря.',
    description: '6 карточек: верх тела + пресс, ягодицы (два уровня), спина + руки и правила занятий.',
    board: 'Тренировки дома',
    tg: TG,
    cards: [
      { title: '4 экспресс-тренировки', image: `${MEDIA}/domashnie-trenirovki-1.jpg` },
      { title: 'Верх тела + пресс', image: `${MEDIA}/domashnie-trenirovki-2.jpg` },
      { title: 'Ягодицы — базовый', image: `${MEDIA}/domashnie-trenirovki-3.jpg` },
      { title: 'Ягодицы — посложнее', image: `${MEDIA}/domashnie-trenirovki-4.jpg` },
      { title: 'Спина + руки', image: `${MEDIA}/domashnie-trenirovki-5.jpg` },
      { title: 'Как заниматься', image: `${MEDIA}/domashnie-trenirovki-6.jpg` },
    ],
  },
  {
    slug: 'metabolic-protocol',
    title: 'Метаболический протокол',
    tagline: 'Домашний режим без жёстких диет: тарелка 80/20, тёплые напитки и 25 минут в день.',
    description: '6 карточек: как собрать тарелку 80/20, тёплые напитки для аппетита, интервалы 25 минут, 15 минут тишины, пряности и распорядок дня.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'Метаболическая тарелка 80/20', image: `${MEDIA}/metabolic-protocol-1.jpg` },
      { title: 'Тёплые напитки', image: `${MEDIA}/metabolic-protocol-2.jpg` },
      { title: 'Интервалы 25 минут', image: `${MEDIA}/metabolic-protocol-3.jpg` },
      { title: '15 минут тишины', image: `${MEDIA}/metabolic-protocol-4.jpg` },
      { title: 'Пряности в рационе', image: `${MEDIA}/metabolic-protocol-5.jpg` },
      { title: 'Распорядок дня', image: `${MEDIA}/metabolic-protocol-6.jpg` },
    ],
  },
  {
    slug: 'domashniy-uhod',
    title: 'Домашний уход и витамины',
    tagline: 'Маски, скрабы и витаминные шоты из того, что уже есть на кухне.',
    description: '6 карточек: витаминные шоты, уход за волосами, маски и тоник для лица, скраб и обёртывание для тела, руки и ноги.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Витаминные шоты', image: `${MEDIA}/domashniy-uhod-1.jpg` },
      { title: 'Волосы: блеск и густота', image: `${MEDIA}/domashniy-uhod-2.jpg` },
      { title: 'Маски для лица', image: `${MEDIA}/domashniy-uhod-3.jpg` },
      { title: 'Скраб и тоник', image: `${MEDIA}/domashniy-uhod-4.jpg` },
      { title: 'Скраб и обёртывание', image: `${MEDIA}/domashniy-uhod-5.jpg` },
      { title: 'Руки и ноги', image: `${MEDIA}/domashniy-uhod-6.jpg` },
    ],
  },
  {
    slug: 'asimetriya',
    title: 'Йога: асимметричное выравнивание',
    tagline: 'Практика для ровной спины и осанки — 30–40 минут на коврике.',
    description: '6 карточек: дыхание 4:4, разминка спины, скручивания, наклоны и вытяжение, балансы и планки, заминка.',
    board: 'Тренировки дома',
    tg: TG,
    cards: [
      { title: 'Дыхание 4:4', image: `${MEDIA}/asimetriya-1.jpg` },
      { title: 'Разминка спины', image: `${MEDIA}/asimetriya-2.jpg` },
      { title: 'Скручивания', image: `${MEDIA}/asimetriya-3.jpg` },
      { title: 'Наклоны и вытяжение', image: `${MEDIA}/asimetriya-4.jpg` },
      { title: 'Балансы и планки', image: `${MEDIA}/asimetriya-5.jpg` },
      { title: 'Заминка', image: `${MEDIA}/asimetriya-6.jpg` },
    ],
  },
  {
    slug: 'pitanie-podskazki',
    title: 'Что и когда есть',
    tagline: 'ГИ, ИИ и три пищевых окна — как время приёма меняет результат.',
    description: '7 карточек: ГИ и ИИ, три пищевых окна, крахмалы, фрукты, ягоды, вечерний разбор и сочетания, снижающие ГИ.',
    board: 'Питание и рецепты',
    tg: TG,
    cards: [
      { title: 'ГИ и ИИ: в чём разница', image: `${MEDIA}/pitanie-podskazki-1.jpg` },
      { title: 'Три пищевых окна', image: `${MEDIA}/pitanie-podskazki-2.jpg` },
      { title: 'Крахмалы: не враг, а с умом', image: `${MEDIA}/pitanie-podskazki-3.jpg` },
      { title: 'Фрукты: когда и сколько', image: `${MEDIA}/pitanie-podskazki-4.jpg` },
      { title: 'Ягоды — лучший выбор', image: `${MEDIA}/pitanie-podskazki-5.jpg` },
      { title: 'Вечер: что можно и что нет', image: `${MEDIA}/pitanie-podskazki-6.jpg` },
      { title: 'Как снизить ГИ блюда', image: `${MEDIA}/pitanie-podskazki-7.jpg` },
    ],
  },
  {
    slug: 'pohudenie-bez-ukolov',
    title: 'Похудение без уколов',
    tagline: 'Естественный путь к весу, который не возвращается.',
    description: '5 карточек: почему вес набирается, белок и сытость, сон и аппетит, силовые для мышц, интервальное голодание 16:8.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Почему вес набирается', image: `${MEDIA}/pohudenie-bez-ukolov-1.jpg` },
      { title: 'Белок — ключ к сытости', image: `${MEDIA}/pohudenie-bez-ukolov-2.jpg` },
      { title: 'Сон — регулятор аппетита', image: `${MEDIA}/pohudenie-bez-ukolov-3.jpg` },
      { title: 'Силовые — сохранить мышцы', image: `${MEDIA}/pohudenie-bez-ukolov-4.jpg` },
      { title: 'Интервальное голодание 16:8', image: `${MEDIA}/pohudenie-bez-ukolov-5.jpg` },
    ],
  },
  {
    slug: 'bady-5',
    title: '5 БАДов с доказательствами',
    tagline: 'Берберин, инозитол, витамин D, омега-3 и магний — что реально работает, а что маркетинг.',
    description: '5 карточек: механизмы и дозировки пяти добавок с доказательной базой, честно про их границы и с дисклеймером.',
    board: 'Здоровье и привычки',
    tg: TG,
    cards: [
      { title: 'Берберин', image: `${MEDIA}/bady-5-1.jpg` },
      { title: 'Инозитол', image: `${MEDIA}/bady-5-2.jpg` },
      { title: 'Витамин D', image: `${MEDIA}/bady-5-3.jpg` },
      { title: 'Омега-3', image: `${MEDIA}/bady-5-4.jpg` },
      { title: 'Магний', image: `${MEDIA}/bady-5-5.jpg` },
    ],
  },
];

export function getLeadMagnet(slug: string): LeadMagnet | undefined {
  return leadMagnets.find((m) => m.slug === slug);
}
