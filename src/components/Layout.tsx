import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import ScrollToHash from './ScrollToHash';

export default function Layout() {
  return (
    <div className="min-h-screen bg-milk text-ink">
      <ScrollToHash />
      <Header />
      <main className="pt-[72px]">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
