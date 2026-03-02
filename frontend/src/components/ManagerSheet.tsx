import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, Upload, FileText, CheckCircle, ExternalLink, RefreshCw } from 'lucide-react';

interface ManagerSheetProps {
    managerId: string;
    batchId: string;
}

const ManagerSheet: React.FC<ManagerSheetProps> = ({ managerId, batchId }) => {
    const [sheetInfo, setSheetInfo] = useState<any>(null);
    const [link, setLink] = useState('');
    const [uploading, setUploading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [mode, setMode] = useState<'view' | 'edit'>('view');

    const fetchSheetInfo = async () => {
        try {
            setLoading(true);
            const res = await axios.get(`http://localhost:5000/api/manager-sheet?manager_id=${managerId}&batch_id=${batchId}`);
            setSheetInfo(res.data);
            if (res.data.sheet_url) {
                setLink(res.data.sheet_url);
            }
            if (!res.data.type) {
                setMode('edit');
            } else {
                setMode('view');
            }
        } catch (error) {
            console.error("Failed to fetch sheet info", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSheetInfo();
    }, [managerId, batchId]);

    const handleSaveLink = async () => {
        try {
            await axios.post('http://localhost:5000/api/manager-sheet/link', {
                manager_id: managerId,
                batch_id: batchId,
                sheet_url: link,
                type: 'link'
            });
            fetchSheetInfo();
        } catch (error) {
            alert("Failed to save link");
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('manager_id', managerId);
        formData.append('batch_id', batchId);

        try {
            setUploading(true);
            await axios.post('http://localhost:5000/api/manager-sheet/upload', formData);
            fetchSheetInfo();
        } catch (error) {
            alert("Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleSyncFeedback = async () => {
        try {
            setSyncing(true);
            const res = await axios.post('http://localhost:5000/api/manager-sheet/sync-feedback', {
                manager_id: managerId,
                batch_id: batchId
            });
            alert(res.data.message);
        } catch (error: any) {
            alert(error.response?.data?.detail || "Sync failed");
        } finally {
            setSyncing(false);
        }
    };

    const getEmbedUrl = (url: string) => {
        if (!url) return '';
        if (url.includes('docs.google.com/spreadsheets')) {
            // Convert to embed/preview link if possible
            if (url.includes('/edit')) {
                return url.split('/edit')[0] + '/preview';
            }
            return url;
        }
        return url;
    };

    if (loading) return <div className="loading-spinner">Loading Resources...</div>;

    return (
        <div className="card" style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <FileText size={24} className="text-primary" /> Manager Worksheets
                    </h2>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Centralized hub for project tracking and external links.</p>
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    {sheetInfo?.type && (
                        <>
                            <button
                                className="btn"
                                style={{ background: 'var(--primary)', color: 'white' }}
                                onClick={() => {
                                    if (sheetInfo.type === 'link') window.open(sheetInfo.sheet_url, '_blank');
                                    else window.open(`http://localhost:5000/${sheetInfo.file_path}`, '_blank');
                                }}
                            >
                                <ExternalLink size={18} /> Open in New Tab
                            </button>
                            <button
                                className="btn"
                                style={{ background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border)' }}
                                onClick={() => setMode(mode === 'view' ? 'edit' : 'view')}
                            >
                                {mode === 'view' ? 'Change Resource' : 'Back to View'}
                            </button>
                        </>
                    )}
                    {sheetInfo?.type === 'link' && (
                        <button
                            className="btn"
                            onClick={handleSyncFeedback}
                            disabled={syncing}
                            style={{
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                color: 'white',
                                opacity: syncing ? 0.7 : 1
                            }}
                        >
                            <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
                            {syncing ? 'Syncing...' : 'Sync Feedback Data'}
                        </button>
                    )}
                    <button className="btn" onClick={fetchSheetInfo} style={{ padding: '0.6rem' }}>
                        <RefreshCw size={18} />
                    </button>
                </div>
            </div>

            {mode === 'edit' || !sheetInfo?.type ? (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '3rem', padding: '2rem' }}>
                    <div style={{ width: '100%', maxWidth: '500px' }}>
                        <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)' }}>
                            <Link size={20} />
                            <h3 style={{ fontWeight: '700' }}>Google Sheets Integration</h3>
                        </div>
                        <div className="input-group" style={{ flexDirection: 'row', gap: '0.5rem' }}>
                            <input
                                type="text"
                                placeholder="Paste Google Sheet Public URL"
                                value={link}
                                onChange={(e) => setLink(e.target.value)}
                                style={{ flex: 1 }}
                            />
                            <button className="btn" onClick={handleSaveLink} disabled={!link}>Link Sheet</button>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                            Ensure the sheet is shared as "Anyone with the link can view" for embedding.
                        </p>
                    </div>

                    <div style={{ width: '100%', maxWidth: '500px', textAlign: 'center' }}>
                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '3rem', position: 'relative' }}>
                            <span style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: '#0f172a', padding: '0 1rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 'bold' }}>OR</span>
                        </div>

                        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--secondary)' }}>
                            <Upload size={20} />
                            <h3 style={{ fontWeight: '700' }}>Upload Excel File</h3>
                        </div>

                        <label className="upload-zone" style={{ cursor: 'pointer', display: 'block' }}>
                            <input type="file" onChange={handleFileUpload} accept=".xlsx, .xls" style={{ display: 'none' }} />
                            <div className="card" style={{ borderStyle: 'dashed', background: 'rgba(255,255,255,0.02)', padding: '2rem' }}>
                                <Upload size={32} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                                <p style={{ fontWeight: '600' }}>{uploading ? 'Uploading...' : 'Drop file here or click to browse'}</p>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Supports .xlsx and .xls formats</p>
                            </div>
                        </label>
                    </div>
                </div>
            ) : (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    {sheetInfo.type === 'link' ? (
                        <div style={{ flex: 1, borderRadius: '1rem', overflow: 'hidden', border: '1px solid var(--border)', background: 'white' }}>
                            <iframe
                                src={getEmbedUrl(sheetInfo.sheet_url)}
                                style={{ width: '100%', height: '100%', border: 'none' }}
                                title="Manager Sheet"
                            />
                        </div>
                    ) : (
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '1.5rem' }}>
                            <div style={{ position: 'relative' }}>
                                <FileText size={80} style={{ color: 'var(--primary)', opacity: 0.3 }} />
                                <CheckCircle size={24} style={{ position: 'absolute', bottom: 0, right: 0, color: '#10b981' }} />
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>{sheetInfo.filename}</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Excel file uploaded and ready.</p>
                            </div>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button className="btn" onClick={() => window.open(`http://localhost:5000/${sheetInfo.file_path}`, '_blank')}>
                                    <ExternalLink size={18} /> Download Excel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ManagerSheet;
