import { useEffect } from 'react';

const SITE_URL = 'https://alina-body.fitness';
const DEFAULT_IMAGE = `${SITE_URL}/images/hero-alina.jpg`;

export type SeoProps = {
  title: string;
  description?: string;
  image?: string;
  path?: string;
  type?: 'website' | 'article';
  jsonLd?: object[];
};

function abs(u?: string) {
  if (!u) return undefined;
  if (/^https?:\/\//.test(u)) return u;
  return SITE_URL + (u.startsWith('/') ? u : `/${u}`);
}

function upsertMeta(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`) as HTMLMetaElement | null;
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function upsertCanonical(href: string) {
  let el = document.head.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', 'canonical');
    document.head.appendChild(el);
  }
  el.setAttribute('href', href);
}

export default function Seo({ title, description, image, path, type = 'website', jsonLd = [] }: SeoProps) {
  const ld = JSON.stringify(jsonLd);

  useEffect(() => {
    document.title = title;
    const desc = description || '';
    const img = abs(image) || DEFAULT_IMAGE;
    const url = path ? SITE_URL + path : `${SITE_URL}/`;

    upsertMeta('name', 'description', desc);
    upsertMeta('property', 'og:title', title);
    upsertMeta('property', 'og:description', desc);
    upsertMeta('property', 'og:image', img);
    upsertMeta('property', 'og:type', type);
    upsertMeta('property', 'og:url', url);
    upsertMeta('property', 'og:site_name', 'Alina Body');
    upsertMeta('name', 'twitter:card', 'summary_large_image');
    upsertMeta('name', 'twitter:title', title);
    upsertMeta('name', 'twitter:description', desc);
    upsertMeta('name', 'twitter:image', img);
    upsertCanonical(url);

    document.head.querySelectorAll('script[data-seo-ld]').forEach((s) => s.remove());
    jsonLd.forEach((obj) => {
      const s = document.createElement('script');
      s.type = 'application/ld+json';
      s.setAttribute('data-seo-ld', '');
      s.textContent = JSON.stringify(obj);
      document.head.appendChild(s);
    });
  }, [title, description, image, path, type, ld]);

  return null;
}
