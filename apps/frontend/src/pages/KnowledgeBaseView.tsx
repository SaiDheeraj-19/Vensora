import React, { useState } from 'react';
import { Upload, FileText, CheckCircle } from 'lucide-react';

export default function KnowledgeBaseView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const token = localStorage.getItem('token');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/v1/knowledge/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Upload failed');
      }

      const data = await res.json();
      setSuccess(`Successfully indexed ${data.chunks_indexed} semantic chunks into Qdrant.`);
      setFile(null);
    } catch (err: any) {
      setError(err.message || 'Network error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2>Knowledge Base Admin</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Upload documentation (.txt) to automatically chunk, embed, and index into the RAG vector store.</p>
      </div>

      <div className="glass-panel" style={{ maxWidth: 600 }}>
        {error && <div style={{ color: 'var(--danger)', marginBottom: 16 }}>{error}</div>}
        {success && (
          <div style={{ color: 'var(--success)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle size={18} /> {success}
          </div>
        )}

        <form onSubmit={handleUpload}>
          <div style={{ 
            border: '2px dashed var(--border-color)', 
            padding: '48px 24px', 
            borderRadius: 8, 
            textAlign: 'center',
            marginBottom: 24
          }}>
            <FileText size={48} color="var(--text-secondary)" style={{ margin: '0 auto 16px' }} />
            <p style={{ marginBottom: 16 }}>Select a text document to embed</p>
            <input 
              type="file" 
              accept=".txt" 
              onChange={(e) => setFile(e.target.files?.[0] || null)} 
              style={{ border: 'none', padding: 0, marginBottom: 0 }}
            />
          </div>
          
          <button type="submit" disabled={!file || uploading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            <Upload size={18} /> 
            {uploading ? 'Processing & Indexing...' : 'Upload to Vector Store'}
          </button>
        </form>
      </div>
    </div>
  );
}
