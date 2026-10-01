import { NavLink, Outlet } from 'react-router-dom';
import DataSourceBanner from '../common/DataSourceBanner.jsx';

const links = [
  ['/', 'Dashboard'],
  ['/materials', 'Materials'],
  ['/predict', 'Predict'],
  ['/discovery', 'Discovery'],
  ['/models', 'Models'],
  ['/experiments', 'Experiments'],
];

export default function Layout() {
  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">AI Materials Discovery</span>
        <nav aria-label="Main">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'}>{label}</NavLink>
          ))}
        </nav>
      </header>
      <main>
        <DataSourceBanner />
        <Outlet />
      </main>
    </div>
  );
}
