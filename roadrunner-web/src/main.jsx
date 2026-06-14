import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import Garage from './pages/Garage';
import RoadRunnerCockpit from './pages/RoadRunnerCockpit';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Garage />} />
        <Route path="/cockpit" element={<RoadRunnerCockpit />} />
        <Route path="/cockpit/:tier" element={<RoadRunnerCockpit />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
