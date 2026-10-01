import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout.jsx';
import Candidates from './pages/Candidates/index.jsx';
import Comparison from './pages/Comparison/index.jsx';
import Dashboard from './pages/Dashboard/index.jsx';
import Discovery from './pages/Discovery/index.jsx';
import Experiments from './pages/Experiments/index.jsx';
import MaterialDetails from './pages/MaterialDetails/index.jsx';
import Materials from './pages/Materials/index.jsx';
import Models from './pages/Models/index.jsx';
import Prediction from './pages/Prediction/index.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="materials" element={<Materials />} />
          <Route path="materials/:id" element={<MaterialDetails />} />
          <Route path="predict" element={<Prediction />} />
          <Route path="discovery" element={<Discovery />} />
          <Route path="discovery/:id" element={<Candidates />} />
          <Route path="compare" element={<Comparison />} />
          <Route path="models" element={<Models />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
