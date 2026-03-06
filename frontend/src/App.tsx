
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

function App() {


  return (
    <Router>
        <Routes>

          <Route path="/" element={<Navigate to="/hearings" replace />} />
          
        </Routes>


    </Router>
  );
}

export default App;