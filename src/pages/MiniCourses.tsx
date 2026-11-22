import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface CourseCard {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  cover_url: string | null;
  price: number;
  currency: string;
  duration_days: number;
  level: string;
  modules_count: number;
  lessons_count: number;
}
interface Category {
  slug: string;
  title: string;
  description: string;
  courses: CourseCard[];
}

export default function MiniCourses() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/mini-course-themes')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('не удалось загрузить'))))
      .then((d) => setCategories(d.categories || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-milk">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-ink/15 border-t-ink" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-milk text-ink">
      <section className="px-5 pt-12 pb-16 sm:px-8">
        <div className="mx-auto max-w-5xl">
          <h1 className="font-display text-4xl sm:text-5xl leading-tight mb-4">Мини-курсы</h1>
          <p className="text-lg text-muted leading-relaxed mb-12 max-w-2xl">
            Пошаговые системы от А до Я — с граммовками, КБЖУ и техниками. Здесь полный контент,
            а не тизер: то, что в соцсетях показывается лишь кусочком.
          </p>

          {error && <p className="text-sm text-[#9a4b43] mb-6">{error}</p>}
          {!error && categories.length === 0 && <p className="text-muted">Курсы скоро появятся.</p>}

          {categories.map((cat) => (
            <div key={cat.slug} className="mb-14">
              <div className="mb-6">
                <h2 className="font-display text-2xl sm:text-3xl">{cat.title}</h2>
                {cat.description && <p className="mt-1 text-sm text-muted">{cat.description}</p>}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {cat.courses.map((c) => (
                  <Link
                    key={c.slug}
                    to={`/course/${c.slug}`}
                    className="group overflow-hidden rounded-2xl border border-ink/5 bg-white transition hover:shadow-lg"
                  >
                    {c.cover_url ? (
                      <img src={c.cover_url} alt={c.title} className="aspect-[3/2] w-full object-cover" />
                    ) : (
                      <div className="aspect-[3/2] w-full bg-blush" />
                    )}
                    <div className="p-5">
                      <h3 className="font-display text-lg leading-snug transition group-hover:text-rose">{c.title}</h3>
                      <p className="mt-1 text-sm text-muted">{c.short_description}</p>
                      <div className="mt-4 flex items-center justify-between">
                        <div className="text-sm text-muted">
                          {c.modules_count} модулей · {c.lessons_count} уроков
                        </div>
                        <div className="font-display text-lg text-rose">
                          {c.price.toLocaleString('ru-RU')} ₽
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
