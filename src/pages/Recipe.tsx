import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send } from 'lucide-react';
import Seo from '../components/Seo';

interface Recipe {
  slug: string;
  name: string;
  category: string;
  ingredients: string;
  method: string;
  image: string;
}

export default function Recipe() {
  const { slug } = useParams<{ slug: string }>();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/recipes.json')
      .then((r) => (r.ok ? r.json() : []))
      .then((data: Recipe[]) => {
        setRecipe(data.find((r) => r.slug === slug) || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-pink-50 to-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Рецепт не найден</h1>
          <Link to="/" className="text-pink-600 hover:text-pink-700">
            ← На главную
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
      <Seo
        title={`${recipe.name} — рецепт | Alina Body`}
        description={`${recipe.name}: ингредиенты и пошаговое приготовление. Простой ПП-рецепт от Алины.`}
        image={recipe.image}
        path={`/recipe/${recipe.slug}`}
        type="website"
      />
      <article className="container mx-auto px-4 py-12 max-w-3xl">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-pink-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          На главную
        </Link>

        {recipe.image && (
          <div className="aspect-[3/4] max-h-[520px] overflow-hidden rounded-2xl mb-8 shadow-lg">
            <img src={recipe.image} alt={recipe.name} className="w-full h-full object-cover" />
          </div>
        )}

        {recipe.category && (
          <span className="inline-block px-3 py-1 bg-pink-100 text-pink-700 text-sm font-semibold rounded-full mb-3">
            {recipe.category}
          </span>
        )}
        <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-8">{recipe.name}</h1>

        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Ингредиенты</h2>
          <p className="text-gray-700 leading-relaxed">{recipe.ingredients}</p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Приготовление</h2>
          <p className="text-gray-700 leading-relaxed">{recipe.method}</p>
        </section>

        <div className="p-8 bg-gradient-to-r from-pink-100 to-pink-50 rounded-2xl border-2 border-pink-200 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Ещё больше рецептов</h2>
          <p className="text-gray-700 mb-6">
            Каждый день — ПП-рецепты, тренировки и советы по осанке в Telegram-канале Алины.
          </p>
          <a
            href="https://t.me/alinabodyfree"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 bg-pink-600 hover:bg-pink-700 text-white font-bold rounded-xl transition-colors"
          >
            <Send className="w-5 h-5" />
            Подписаться на Telegram →
          </a>
        </div>
      </article>
    </div>
  );
}
