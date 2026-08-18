export async function api<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;

  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data && data.error) || 'Не получилось выполнить запрос');
  }
  return data as T;
}

export function formatPrice(value: number) {
  return `${new Intl.NumberFormat('ru-RU').format(value)} ₽`;
}

export type Tariff = {
  id: number;
  program_id: number;
  slug: string;
  name: string;
  price: number;
  access_days: number;
  description: string;
  features: string[];
  is_popular: boolean;
  sort_order: number;
};

export type Program = {
  id: number;
  slug: string;
  title: string;
  short_title: string;
  type: string;
  tagline: string;
  description: string;
  duration_label: string;
  price: number;
  next_start: string;
  seats_note: string;
  image_url: string;
  video_count: number;
  session_minutes: string;
  highlights: string[];
  is_featured: boolean;
  sort_order: number;
  tariffs: Tariff[];
};

export type Review = {
  id: number;
  author_name: string;
  author_age: number;
  city: string;
  program_title: string;
  quote: string;
  result_note: string;
};

export type Faq = {
  id: number;
  question: string;
  answer: string;
};

export type Lesson = {
  id: number;
  program_id: number;
  week: number;
  day: number;
  title: string;
  duration_min: number;
  description: string;
  video_url: string | null;
  is_preview: boolean;
  locked: boolean;
  sort_order: number;
};

export type Material = {
  id: number;
  program_id: number;
  title: string;
  description: string;
  file_url: string | null;
  file_type: string;
  locked: boolean;
};

export type Enrollment = {
  id: number;
  user_id: string;
  program_id: number;
  tariff_id: number;
  order_id: number;
  access_until: string;
  created_at: string;
  program: Program | null;
  tariff: Tariff | null;
};

export type ProgressRow = {
  id: number;
  user_id: string;
  lesson_id: number;
  completed: boolean;
  completed_at: string | null;
};

export type TrackerRow = {
  id: number;
  user_id: string;
  program_id: number;
  day_number: number;
  mood: string;
  energy: number;
  note: string;
  logged_at: string;
};
