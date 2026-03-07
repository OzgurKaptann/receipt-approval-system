import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { ReceiptsList } from './pages/ReceiptsList';
import { ReceiptDetail } from './pages/ReceiptDetail';
import { Settings } from './pages/Settings';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/receipts" element={<ReceiptsList />} />
        <Route path="/receipts/:id" element={<ReceiptDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
