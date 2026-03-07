import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { fetchApi } from '@/services/api';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { ArrowLeft, CheckCircle, XCircle, FileImage, ShieldCheck, Clock, User } from 'lucide-react';

interface DocumentDetail {
  id: string;
  public_key: string;
  status: string;
  customer_id: string;
  original_file_name: string;
  file_size: number;
  mime_type: string;
  sender_name?: string;
  amount_try?: number;
  transfer_date?: string;
  created_at: string;
  ocr_raw_data?: Record<string, any>;
  slack_decided_by?: string;
}

export function ReceiptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocument();
  }, [id]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      const data = await fetchApi(`/documents/${id}`);
      setDoc(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load document details');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: 'approve' | 'reject') => {
    if (!confirm(`Are you sure you want to FORCE ${action.toUpperCase()} this document?`)) return;
    try {
      setActionLoading(true);
      const updated = await fetchApi(`/documents/${id}/${action}`, {
        method: 'POST'
      });
      setDoc(updated);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'UPLOADED':
      case 'TG_PENDING':
      case 'SLACK_PENDING':
        return <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">Awaiting Review</span>;
      case 'SLACK_APPROVED':
      case 'APPROVED':
      case 'DEPOSIT_SUCCESS':
        return <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-500/10 text-green-400 border border-green-500/20">Approved / Success</span>;
      case 'OCR_FAILED':
      case 'TG_REJECTED':
      case 'SLACK_REJECTED':
      case 'DEPOSIT_FAILED':
      case 'REJECTED':
        return <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20">Failed / Rejected</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-500/10 text-gray-400 border border-gray-500/20">{status}</span>;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-full items-center justify-center">
          <div className="w-8 h-8 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
        </div>
      </Layout>
    );
  }

  if (error || !doc) {
    return (
      <Layout>
        <div className="m-8 p-6 glass rounded-2xl flex flex-col items-center justify-center space-y-4">
          <XCircle className="w-16 h-16 text-red-500" />
          <h2 className="text-xl font-bold">{error || "Document not found"}</h2>
          <button onClick={() => navigate('/receipts')} className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition">Go Back</button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8 max-w-[1600px] mx-auto space-y-6">
        {/* Header Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/receipts')}
              className="p-2 hover:bg-white/5 rounded-full transition"
            >
              <ArrowLeft className="w-6 h-6 text-gray-400" />
            </button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Receipt Details</h1>
              <p className="text-sm text-gray-400">ID: {doc.id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {getStatusBadge(doc.status)}
            
            {(doc.status === 'UPLOADED' || doc.status.includes('PENDING')) && (
              <div className="flex items-center space-x-2 border-l border-white/10 pl-4 ml-4">
                <button
                  onClick={() => handleAction('reject')}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg font-medium hover:bg-red-500/20 transition disabled:opacity-50 flex items-center shadow-[0_0_15px_rgba(239,68,68,0.1)]"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Force Reject
                </button>
                <button
                  onClick={() => handleAction('approve')}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg font-medium hover:bg-green-500/30 transition disabled:opacity-50 flex items-center shadow-[0_0_15px_rgba(34,197,94,0.15)]"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Force Approve
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Split Screen Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-180px)]">
          
          {/* Left Panel: Image Viewer */}
          <div className="glass rounded-2xl flex flex-col overflow-hidden relative group">
            <div className="p-4 border-b border-white/5 flex items-center space-x-2 bg-black/20">
              <FileImage className="w-5 h-5 text-gray-400" />
              <span className="font-semibold">{doc.original_file_name}</span>
              <span className="text-xs text-gray-400 ml-auto">{(doc.file_size / 1024).toFixed(1)} KB</span>
            </div>
            <div className="flex-1 bg-black/50 p-4 relative overflow-auto flex items-center justify-center">
              <img 
                src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/documents/${doc.id}/image`} 
                alt="Receipt Original"
                className="max-w-full h-auto object-contain rounded drop-shadow-2xl"
              />
            </div>
          </div>

          {/* Right Panel: Data and Logs */}
          <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar">
            
            <div className="glass rounded-2xl p-6 space-y-6">
              <h3 className="text-lg font-semibold flex items-center mb-4">
                <ShieldCheck className="w-5 h-5 mr-2 text-primary" />
                Parsed Information
              </h3>
              
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sender Name</label>
                  <p className="font-medium text-lg mt-1">{doc.sender_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Matched Amount</label>
                  <p className="font-bold text-xl mt-1 text-green-400">
                    {doc.amount_try ? `₺${doc.amount_try}` : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Date on Receipt</label>
                  <div className="flex items-center mt-1">
                    <Clock className="w-4 h-4 text-gray-400 mr-2" />
                    <span>{doc.transfer_date ? format(new Date(doc.transfer_date), 'dd MMM yyyy, HH:mm', { locale: tr }) : 'N/A'}</span>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Customer Ref</label>
                  <div className="flex items-center mt-1">
                    <User className="w-4 h-4 text-gray-400 mr-2" />
                    <span className="truncate" title={doc.customer_id}>{doc.customer_id.split('-')[0]}...</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass rounded-2xl p-6 flex-1 flex flex-col">
              <h3 className="text-lg font-semibold mb-4">OCR Raw Payload Analysis</h3>
              <div className="flex-1 bg-black/50 rounded-xl p-4 overflow-auto overflow-x-auto border border-white/5 custom-scrollbar">
                {doc.ocr_raw_data ? (
                  <pre className="text-sm font-mono text-blue-300">
                    {JSON.stringify(doc.ocr_raw_data, null, 2)}
                  </pre>
                ) : (
                  <div className="flex h-full items-center justify-center text-gray-500">
                    No raw OCR data available for this document.
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </Layout>
  );
}
