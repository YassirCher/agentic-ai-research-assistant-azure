import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiUrl } from '../lib/apiClient';

export default function PDFUploader({ onUploadSuccess }) {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, success, error
  const [progress, setProgress] = useState(0);
  const [fileResults, setFileResults] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setStatus('uploading');
    setProgress(0);
    setErrorMessage('');
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file); // 'files' matching backend List[UploadFile]
    });

    try {
      const data = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', apiUrl('/api/upload'));

        xhr.upload.onprogress = (event) => {
          if (!event.lengthComputable) return;
          const pct = Math.round((event.loaded * 100) / event.total);
          setProgress(pct);
        };

        xhr.onload = () => {
          try {
            const payload = JSON.parse(xhr.responseText || '{}');
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(payload);
              return;
            }
            reject(payload);
          } catch (_) {
            reject({ detail: { message: 'Reponse serveur invalide' } });
          }
        };

        xhr.onerror = () => reject({ detail: { message: 'Erreur reseau pendant upload' } });
        xhr.send(formData);
      });

      setFileResults(data.files || []);
      setStatus('processing');
      onUploadSuccess?.();
      sessionStorage.setItem(`uploadStatusUrl:${data.chat_id}`, data.status_url || '');
      navigate(`/c/${data.chat_id}`, {
        state: {
          uploadStatusUrl: data.status_url,
        },
      });
    } catch (err) {
      console.error(err);
      setFileResults(err?.detail?.files || []);
      setErrorMessage(err?.detail?.message || 'Une erreur est survenue lors de l\'upload.');
      setStatus('error');
    }
  };

  return (
    <div className="upload-section">
      <div className="upload-box" onClick={() => document.getElementById('pdf-input').click()}>
        <input 
          id="pdf-input" 
          type="file" 
          accept=".pdf" 
          multiple
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
        {status === 'success' ? (
          <CheckCircle size={48} color="#10b981" style={{ margin: '0 auto', marginBottom: '1rem' }} />
        ) : status === 'uploading' ? (
          <Loader2 size={48} className="animate-spin" color="var(--accent-primary)" style={{ margin: '0 auto', marginBottom: '1rem' }} />
        ) : status === 'processing' ? (
          <Loader2 size={48} className="animate-spin" color="var(--accent-primary)" style={{ margin: '0 auto', marginBottom: '1rem' }} />
        ) : files.length > 0 ? (
          <FileText size={48} color="var(--accent-primary)" style={{ margin: '0 auto', marginBottom: '1rem' }} />
        ) : (
          <UploadCloud size={48} color="var(--text-muted)" style={{ margin: '0 auto', marginBottom: '1rem' }} />
        )}
        
        <p style={{ fontWeight: 600 }}>
          {status === 'success' ? 'Documents Indexés' : 
           status === 'uploading' ? 'Indexation en cours...' :
            status === 'processing' ? 'Traitement en arrière-plan...' :
           files.length > 0 ? `${files.length} fichier(s) sélectionné(s)` : 
           'Cliquez pour uploader des PDF'}
        </p>
      </div>

      {files.length > 0 && status === 'idle' && (
        <button 
          className="upload-btn" 
          onClick={handleUpload}
        >
          Lancer la Recherche sur {files.length} document(s)
        </button>
      )}

      {status === 'uploading' && (
        <div style={{ marginTop: '1rem' }}>
          <div
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '999px',
              background: 'rgba(148, 163, 184, 0.2)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${progress}%`,
                height: '100%',
                borderRadius: '999px',
                background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-hover))',
                transition: 'width 0.2s ease',
              }}
            />
          </div>
          <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
            Upload en cours: {progress}%
          </p>
        </div>
      )}

      {fileResults.length > 0 && (
        <div style={{ marginTop: '1rem', display: 'grid', gap: '0.5rem' }}>
          {fileResults.map((item, idx) => (
            <div
              key={`${item.filename}-${idx}`}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: '1rem',
                border: '1px solid var(--border-color)',
                borderRadius: '0.75rem',
                padding: '0.6rem 0.8rem',
                fontSize: '0.82rem',
              }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.filename}</span>
              <span style={{ color: item.status === 'indexed' ? '#10b981' : '#ef4444' }}>{item.status}</span>
            </div>
          ))}
        </div>
      )}
      
      {status === 'error' && (
        <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '1rem', textAlign: 'center' }}>
          {errorMessage || 'Une erreur est survenue lors de l\'upload. Réessayez.'}
        </p>
      )}
    </div>
  );
}
