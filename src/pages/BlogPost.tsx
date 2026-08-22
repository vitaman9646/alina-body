import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, Clock } from 'lucide-react';

interface Post {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  cover_image: string;
  published_at: string;
}

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;

    fetch(`/api/posts?slug=${slug}`)
      .then(res => {
        if (!res.ok) throw new Error('Article not found');
        return res.json();
      })
      .then(data => {
        setPost(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading post:', err);
        setLoading(false);
      });
  }, [slug]);

  useEffect(() => {
    if (post) {
      document.title = `${post.title} — Alina Body`;
    }
  }, [post]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-pink-50 to-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Статья не найдена</h1>
          <Link to="/blog" className="text-pink-600 hover:text-pink-700">
            ← Вернуться к статьям
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
      <article className="container mx-auto px-4 py-12 max-w-4xl">
        <Link
          to="/blog"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-pink-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Все статьи
        </Link>

        {post.cover_image && (
          <div className="aspect-video rounded-2xl overflow-hidden mb-8 shadow-lg">
            <img
              src={post.cover_image}
              alt={post.title}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4">
          {post.title}
        </h1>

        <div className="flex items-center gap-4 text-gray-500 mb-8">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            {new Date(post.published_at).toLocaleDateString('ru-RU', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            7 мин чтения
          </div>
        </div>

        <div
          className="prose prose-lg max-w-none prose-pink"
          dangerouslySetInnerHTML={{ __html: post.content }}
        />

        {/* CTA блок на курс */}
        <div className="mt-16 p-8 bg-gradient-to-r from-pink-100 to-pink-50 rounded-2xl border-2 border-pink-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Хочешь продолжить?
          </h2>
          <p className="text-gray-700 mb-6">
            Здесь была только верхушка айсберга. Полный курс с пошаговым планом, 
            видео-уроками и персональной поддержкой — это то, что реально меняет тело и привычки.
          </p>
          <Link
            to="/courses/start-home"
            className="inline-block px-8 py-4 bg-pink-600 hover:bg-pink-700 text-white font-bold rounded-xl transition-colors"
          >
            Узнать подробнее →
          </Link>
        </div>

        {/* Дисклеймер */}
        <div className="mt-8 p-4 bg-gray-100 rounded-xl text-sm text-gray-600">
          <strong>Важно:</strong> Перед началом любых тренировок проконсультируйтесь с врачом, 
          особенно если у вас есть хронические заболевания или травмы.
        </div>
      </article>
    </div>
  );
  }
