import { useState, useEffect } from 'react';
import axios from 'axios';
import { Home, BarChart2, MessageSquare, Users, BookOpen, Settings as SettingsIcon, Trash2 } from 'lucide-react';
import FileUpload from './components/FileUpload';
import InternGrid from './components/InternGrid';
import ChatBot from './components/ChatBot';
import BatchDashboard from './components/BatchDashboard';
import GlobalDashboard from './components/GlobalDashboard';
import Settings from './components/Settings';
import { Globe } from 'lucide-react';
import { API_BASE_URL } from './config';
import { loginRequest } from './authConfig';
import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('global');
  const [data, setData] = useState([]);
  const [manager, setManager] = useState<any>(null);
  const [batches, setBatches] = useState<any[]>([]);
  const [activeBatch, setActiveBatch] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);

  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [newBatchName, setNewBatchName] = useState('');
  const [activeDepartment, setActiveDepartment] = useState<'Data Ops' | 'Data Engineering'>('Data Ops');
  const [isCreatingBatch, setIsCreatingBatch] = useState(false);
  const [isDeletingBatch, setIsDeletingBatch] = useState(false);
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'ai', text: string }[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  useEffect(() => {
    if (isAuthenticated && accounts.length > 0) {
      const activeAccount = accounts[0];
      const roles = activeAccount.idTokenClaims?.roles || [];
      setManager({
        name: activeAccount.name || "Unknown User",
        manager_id: activeAccount.idTokenClaims?.preferred_username || activeAccount.username,
        username: activeAccount.username,
        roles: roles
      });
    } else {
      setManager(null);
    }
  }, [isAuthenticated, accounts]);

  useEffect(() => {
    const reqInterceptor = axios.interceptors.request.use(async (config) => {
      if (isAuthenticated && accounts.length > 0) {
        try {
          const response = await instance.acquireTokenSilent({
            ...loginRequest,
            account: accounts[0]
          });
          config.headers.Authorization = `Bearer ${response.idToken}`;
        } catch (error) {
          console.error("Failed to acquire token silently", error);
        }
      }
      return config;
    }, (error) => {
      return Promise.reject(error);
    });

    return () => {
      axios.interceptors.request.eject(reqInterceptor);
    }
  }, [instance, accounts, isAuthenticated]);

  const handleLogin = () => {
    instance.loginRedirect(loginRequest).catch(e => console.error(e));
  };

  const handleLogout = () => {
    instance.logoutRedirect({
      postLogoutRedirectUri: "/",
    });
  };

  const roles = manager?.roles || [];
  const canEdit = roles.map((r: string) => r.toLowerCase()).includes('ldmanager') || roles.map((r: string) => r.toLowerCase()).includes('admin');

  const fetchData = async () => {
    if (!manager || !activeBatch) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/api/scores?manager_id=${manager.manager_id}&batch_id=${activeBatch.batch_id}`);
      setData(res.data);
    } catch (error) {
      console.error("Failed to fetch data", error);
    }
  };

  const fetchBatches = async () => {
    if (!manager) return;
    try {
      console.log("Fetching batches for:", manager.manager_id, activeDepartment);
      const res = await axios.get(`${API_BASE_URL}/api/batches?manager_id=${manager.manager_id}&department=${activeDepartment}`);
      console.log("Batches received:", res.data);
      setBatches(res.data);
      if (!activeBatch && res.data.length > 0) {
        setActiveBatch(res.data[0]);
      }
    } catch (error: any) {
      console.error("Batch fetch failed:", error);
      alert("API Error: Unable to fetch batches. Check if backend is running on port 5000.");
    }
  };



  const fetchSubjects = async () => {
    if (!manager || !activeBatch) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/api/subjects?manager_id=${manager.manager_id}&batch_id=${activeBatch.batch_id}`);
      setSubjects(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const createBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBatchName || isCreatingBatch) return;
    setIsCreatingBatch(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/batches`, {
        name: newBatchName,
        manager_id: manager.manager_id,
        department: activeDepartment
      });
      setNewBatchName('');
      setShowBatchModal(false);

      const batchesRes = await axios.get(`${API_BASE_URL}/api/batches?manager_id=${manager.manager_id}&department=${activeDepartment}`);
      setBatches(batchesRes.data);

      const newlyCreated = batchesRes.data.find((b: any) => b.batch_id === res.data.batch_id);
      if (newlyCreated) setActiveBatch(newlyCreated);
    } catch (error) {
      console.error(error);
      alert("Failed to create workspace. Check the server connection.");
    } finally {
      setIsCreatingBatch(false);
    }
  };



  useEffect(() => {
    fetchData();
  }, [manager, activeBatch]);

  useEffect(() => {
    if (manager) {
      setActiveBatch(null); // Clear context when switching portals
      setData([]);
      setSubjects([]);
      setChatHistory([]); // Clear chat when switching departments
      setCurrentSessionId(null);
      fetchBatches();
    }
  }, [manager, activeDepartment]);

  useEffect(() => {
    if (manager && activeBatch) {
      fetchSubjects();
    }
  }, [manager, activeBatch]);

  if (!manager) {
    return (
      <div className="auth-container">
        <div className="card auth-card" style={{ textAlign: 'center' }}>
          <div className="auth-header">
            <h2>Welcome to Sigmoid</h2>
          </div>
          <button className="btn" style={{ width: '100%', padding: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: '#0078D4' }} onClick={handleLogin}>
            Sign In with Microsoft
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="sidebar">
        <div>
          <h1 style={{ marginBottom: '0.1rem' }}>L&D Portal</h1>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.3rem', borderRadius: '0.75rem', display: 'flex', gap: '0.3rem', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
            <button
              onClick={() => setActiveDepartment('Data Ops')}
              style={{
                flex: 1, padding: '0.5rem', borderRadius: '0.5rem', border: 'none', fontSize: '0.75rem', fontWeight: '700', cursor: 'pointer', transition: 'all 0.2s',
                background: activeDepartment === 'Data Ops' ? 'var(--primary)' : 'transparent',
                color: activeDepartment === 'Data Ops' ? 'white' : 'var(--text-muted)',
                boxShadow: activeDepartment === 'Data Ops' ? '0 2px 8px rgba(99,102,241,0.3)' : 'none'
              }}
            >
              Data Ops
            </button>
            <button
              onClick={() => setActiveDepartment('Data Engineering')}
              style={{
                flex: 1, padding: '0.5rem', borderRadius: '0.5rem', border: 'none', fontSize: '0.75rem', fontWeight: '700', cursor: 'pointer', transition: 'all 0.2s',
                background: activeDepartment === 'Data Engineering' ? 'var(--secondary)' : 'transparent',
                color: activeDepartment === 'Data Engineering' ? 'white' : 'var(--text-muted)',
                boxShadow: activeDepartment === 'Data Engineering' ? '0 2px 8px rgba(52,211,153,0.3)' : 'none'
              }}
            >
              DE Track
            </button>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700' }}>Active Batch</p>
              {canEdit && (
                <button
                  onClick={() => setShowBatchModal(true)}
                  style={{ background: 'rgba(147, 51, 234, 0.1)', border: '1px solid rgba(147, 51, 234, 0.2)', color: 'var(--primary)', padding: '0.2rem 0.5rem', borderRadius: '0.4rem', fontSize: '0.7rem', fontWeight: '700', cursor: 'pointer' }}
                >
                  + ADD NEW BATCH
                </button>
              )}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <select
                value={activeBatch?.batch_id || ''}
                onChange={(e) => setActiveBatch(batches.find(b => b.batch_id === e.target.value))}
                style={{ flex: 1, padding: '0.75rem', borderRadius: '0.75rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', color: 'white', fontWeight: '600' }}
              >
                <option value="">-- Choose Batch --</option>
                {batches.map(b => (
                  <option key={b.batch_id} value={b.batch_id}>
                    {b.name}
                  </option>
                ))}
              </select>
              {canEdit && activeBatch && (
                <button
                  onClick={() => setShowDeleteModal(true)}
                  title="Delete Batch"
                  style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#ef4444', padding: '0 0.8rem', borderRadius: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s' }}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '0.75rem', marginBottom: '2rem', border: '1px solid var(--border)' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700', marginBottom: '0.25rem' }}>Active Manager Details</p>
            <p style={{ color: 'white', fontWeight: '600', wordBreak: 'break-all', fontSize: '0.85rem' }}>ID: {manager.manager_id}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.25rem' }}>Roles: {manager.roles?.join(', ') || 'No Roles Assigned'}</p>
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          <button className={`nav-link ${activeTab === 'global' ? 'active' : ''}`} onClick={() => setActiveTab('global')}>
            <Globe size={18} /> Dashboard
          </button>

          <div style={{ margin: '1rem 0', height: '1px', background: 'var(--border)' }}></div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700', padding: '0 1rem', marginBottom: '0.5rem' }}>Batch Tools</p>

          <button className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')} disabled={!activeBatch}>
            <Home size={18} /> Batch Summary
          </button>
          <button className={`nav-link ${activeTab === 'scores' ? 'active' : ''}`} onClick={() => setActiveTab('scores')} disabled={!activeBatch}>
            <BarChart2 size={18} /> Scores
          </button>
          <button className={`nav-link ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')} disabled={!activeBatch}>
            <MessageSquare size={18} /> Chatbot
          </button>
          <button className={`nav-link ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')} disabled={!activeBatch}>
            <SettingsIcon size={18} /> Grading Rules
          </button>
        </nav>

        <button
          className="btn"
          style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.2)' }}
          onClick={handleLogout}
        >
          Sign Out
        </button>
      </div>

      <main className="main-content">
        {activeTab === 'global' ? (
          <GlobalDashboard managerId={manager.manager_id} activeDepartment={activeDepartment} />
        ) : !activeBatch ? (
          <div className="card" style={{ textAlign: 'center', marginTop: '10rem', background: 'rgba(147, 51, 234, 0.05)', borderStyle: 'dashed' }}>
            <BookOpen size={48} style={{ color: 'var(--primary)', marginBottom: '1.5rem', opacity: 0.5 }} />
            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>No Active Batch</h2>
            <p style={{ color: 'var(--text-muted)', maxWidth: '400px', margin: '0 auto 1.5rem' }}>Switch context by selecting an existing batch or create a new one to start tracking performance.</p>
            <button className="btn" onClick={() => setShowBatchModal(true)}>Create First Batch</button>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div>
                <div className="stat-grid">
                  <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                      <Users size={16} />
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Interns</span>
                    </div>
                    <p style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--primary)', lineHeight: '1' }}>{data.length}</p>
                  </div>
                  {canEdit && (
                    <FileUpload endpoint="upload-interns" label="Upload Data" onSuccess={fetchData} managerId={manager.manager_id} batchId={activeBatch.batch_id} />
                  )}
                </div>

                <div className="card" style={{ background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.1) 0%, rgba(30, 41, 59, 0) 100%)', marginBottom: '2rem' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.5rem' }}>Current Batch: {activeBatch.name}</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '600px' }}>
                    Track and manage performance metrics, detailed scoring, and AI-powered recommendations for all interns in this batch.
                  </p>
                </div>

                <BatchDashboard
                  data={data}
                  subjects={subjects}
                  managerId={manager.manager_id}
                  batchId={activeBatch.batch_id}
                />
              </div>
            )}

            {activeTab === 'scores' && (
              <InternGrid data={data} managerId={manager.manager_id} batchId={activeBatch.batch_id} />
            )}

            {activeTab === 'chat' && (
              <ChatBot
                managerId={manager.manager_id}
                batchId={activeBatch.batch_id}
                messages={chatHistory}
                setMessages={setChatHistory}
                sessionId={currentSessionId}
                setSessionId={setCurrentSessionId}
              />
            )}
            {activeTab === 'settings' && (
              <Settings managerId={manager.manager_id} batchId={activeBatch.batch_id} />
            )}
          </>
        )}
      </main>

      {showBatchModal && (
        <div className="modal-overlay" onClick={() => setShowBatchModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', textAlign: 'center' }}>
            <div style={{ background: 'var(--primary)', width: '64px', height: '64px', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', boxShadow: '0 10px 30px rgba(99,102,241,0.4)' }}>
              <BookOpen size={32} color="white" />
            </div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: '800', marginBottom: '0.5rem' }}>New Batch</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9375rem' }}>Define a new workspace to isolate intern performance records.</p>

            <form onSubmit={createBatch}>
              <div className="input-group">
                <label style={{ textAlign: 'left', display: 'block' }}>Batch Identifier</label>
                <input
                  type="text"
                  placeholder={`e.g. Q1 ${activeDepartment} 2024`}
                  value={newBatchName}
                  onChange={e => setNewBatchName(e.target.value)}
                  autoFocus
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '2.5rem' }}>
                <button className="btn" type="submit" style={{ flex: 1, padding: '1rem' }} disabled={isCreatingBatch}>
                  {isCreatingBatch ? 'Initializing...' : 'Initialize Batch'}
                </button>
              </div>
            </form>
            <button onClick={() => setShowBatchModal(false)} style={{ marginTop: '1rem', background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.875rem', cursor: 'pointer' }} disabled={isCreatingBatch}>
              Maybe later
            </button>
          </div>
        </div>
      )}

      {showDeleteModal && (
        <div className="modal-overlay" onClick={() => !isDeletingBatch && setShowDeleteModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', textAlign: 'center' }}>
            <div style={{ background: '#ef4444', width: '64px', height: '64px', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', boxShadow: '0 10px 30px rgba(239,68,68,0.4)' }}>
              <Trash2 size={32} color="white" />
            </div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: '800', marginBottom: '0.5rem' }}>Delete Batch?</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9375rem' }}>
              Are you sure you want to permanently delete <strong>{activeBatch?.name}</strong>? This will remove all associated interns, scores, settings, and feedback records. This action cannot be undone.
            </p>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button
                className="btn"
                style={{ flex: 1, padding: '1rem', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeletingBatch}
              >
                Cancel
              </button>
              <button
                className="btn"
                style={{ flex: 1, padding: '1rem', background: '#ef4444', color: 'white', boxShadow: 'none' }}
                onClick={async () => {
                  setIsDeletingBatch(true);
                  try {
                    await axios.delete(`${API_BASE_URL}/api/batches/${activeBatch.batch_id}?manager_id=${manager.manager_id}`);
                    const newBatches = batches.filter(b => b.batch_id !== activeBatch.batch_id);
                    setBatches(newBatches);
                    setActiveBatch(newBatches.length > 0 ? newBatches[0] : null);
                    setData([]);
                    setSubjects([]);

                    setActiveTab('global');
                    setShowDeleteModal(false);
                  } catch (e) {
                    console.error("Failed to delete batch", e);
                    alert("Failed to delete workspace. Please try again.");
                  } finally {
                    setIsDeletingBatch(false);
                  }
                }}
                disabled={isDeletingBatch}
              >
                {isDeletingBatch ? 'Deleting...' : 'Yes, Delete It'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
