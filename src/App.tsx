import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Learn = lazy(() => import('./pages/Learn'));
const Auth = lazy(() => import('./pages/Auth'));
const Terms = lazy(() => import('./pages/Terms'));
const Privacy = lazy(() => import('./pages/Privacy'));
const Blog = lazy(() => import('./pages/Blog'));
const BlogPost = lazy(() => import('./pages/BlogPost'));
const LeadMagnet = lazy(() => import('./pages/LeadMagnet'));
const Recipe = lazy(() => import('./pages/Recipe'));
const CourseLanding = lazy(() => import('./pages/CourseLanding'));
const MiniCourses = lazy(() => import('./pages/MiniCourses'));
const Tarify = lazy(() => import('./pages/Tarify'));
const Contact = lazy(() => import('./pages/Contact'));

function PageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-ink/15 border-t-ink" />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Home />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/:slug" element={<BlogPost />} />
              <Route path="/lead/:slug" element={<LeadMagnet />} />
              <Route path="/recipe/:slug" element={<Recipe />} />
              <Route path="/course/:slug" element={<CourseLanding />} />
              <Route path="/courses" element={<MiniCourses />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/tarify" element={<Tarify />} />
              <Route path="/contacts" element={<Contact />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/learn/:slug"
                element={
                  <ProtectedRoute>
                    <Learn />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}
