export function mapCourse(c) {
  const isChallenge =
    (c.slug && String(c.slug).includes('challenge')) ||
    (c.level && String(c.level).includes('challenge'));
  const isFree = Boolean(c.is_free);

  return {
    id: c.id,
    slug: c.slug,
    title: c.title,
    short_title: c.short_description || c.title,
    type: isChallenge ? 'challenge' : 'course',
    tagline: c.short_description || '',
    description: c.description || c.short_description || '',
    duration_label: c.duration_days ? `${c.duration_days} дней` : '',
    price: Number(c.price) || 0,
    next_start: '',
    seats_note: isFree ? 'Бесплатный тест' : '',
    image_url: c.cover_url || '',
    video_count: 0,
    session_minutes: '',
    highlights: c.short_description ? [c.short_description] : [],
    is_featured: true,
    sort_order: c.sort_order ?? 0,
    tariffs: [
      {
        id: 1,
        program_id: c.id,
        slug: 'default',
        name: isFree ? 'Бесплатно' : 'Стандарт',
        price: Number(c.price) || 0,
        access_days: c.duration_days || 30,
        description: c.short_description || '',
        features: [],
        is_popular: true,
        sort_order: 1,
      },
    ],
  };
}

export function accessUntil(paidAt, days) {
  if (!paidAt) return null;
  const d = new Date(paidAt);
  d.setDate(d.getDate() + Number(days || 30));
  return d.toISOString();
}
