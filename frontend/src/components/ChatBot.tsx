import React, { useState } from 'react';
import axios from 'axios';
import { Send, Bot, User, History, Plus, ChevronLeft, ChevronRight, Pencil, Check, X, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from '../config';

interface Props {
    managerId: string;
    batchId: string;
    messages: { role: 'user' | 'ai', text: string }[];
    setMessages: React.Dispatch<React.SetStateAction<{ role: 'user' | 'ai', text: string }[]>>;
    sessionId: string | null;
    setSessionId: (id: string | null) => void;
}

const ChatBot: React.FC<Props> = ({ managerId, batchId, messages, setMessages, sessionId, setSessionId }) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessions, setSessions] = useState<any[]>([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState('');

    const fetchSessions = async () => {
        try {
            const res = await axios.get(`${API_BASE_URL}/api/chat/sessions?manager_id=${managerId}&batch_id=${batchId}`);
            setSessions(res.data);
        } catch (error) {
            console.error("Failed to fetch sessions", error);
        }
    };

    const fetchMessages = async (sId: string) => {
        try {
            setLoading(true);
            const res = await axios.get(`${API_BASE_URL}/api/chat/session/${sId}`);
            setMessages(res.data);
            setSessionId(sId);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleRename = async (sId: string) => {
        if (!editTitle) return;
        try {
            await axios.put(`${API_BASE_URL}/api/chat/session/${sId}`, { title: editTitle });
            setEditingSessionId(null);
            fetchSessions();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDeleteSession = async (e: React.MouseEvent, sId: string) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this chat history?")) return;
        try {
            await axios.delete(`${API_BASE_URL}/api/chat/session/${sId}`);
            if (sId === sessionId) {
                setMessages([]);
                setSessionId(null);
            }
            fetchSessions();
        } catch (error) {
            console.error(error);
        }
    };

    React.useEffect(() => {
        fetchSessions();
    }, [batchId]);

    const handleSend = async () => {
        if (!query) return;
        const userMsg = query;
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setQuery('');
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:5000/api/chat', {
                query: userMsg,
                manager_id: managerId,
                batch_id: batchId,
                history: messages,
                session_id: sessionId
            });
            setMessages(prev => [...prev, { role: 'ai', text: res.data.response }]);
            if (!sessionId) {
                setSessionId(res.data.session_id);
                fetchSessions();
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'ai', text: "Sorry, I'm having trouble connecting to the brain." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setSessionId(null);
    };

    return (
        <div style={{ display: 'flex', gap: '1.5rem', height: '600px', position: 'relative' }}>
            {/* History Sidebar */}
            <div
                className="card"
                style={{
                    width: isSidebarOpen ? '280px' : '0px',
                    padding: isSidebarOpen ? '1.25rem' : '0px',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    opacity: isSidebarOpen ? 1 : 0,
                    background: 'rgba(255,255,255,0.05)',
                    border: isSidebarOpen ? '1px solid var(--border)' : 'none'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <History size={18} style={{ color: 'var(--primary)' }} />
                        <h3 style={{ fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>History</h3>
                    </div>
                </div>

                <button
                    onClick={handleNewChat}
                    style={{
                        width: '100%',
                        padding: '0.75rem',
                        borderRadius: '0.75rem',
                        border: '1px dashed var(--primary)',
                        background: 'rgba(147, 51, 234, 0.05)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        marginBottom: '1.5rem',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        color: 'var(--primary)',
                        fontWeight: '600'
                    }}
                >
                    <Plus size={16} /> New Chat
                </button>

                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem', paddingRight: '0.5rem' }}>
                    {sessions.map((s) => (
                        <div
                            key={s.session_id}
                            style={{
                                padding: '0.75rem',
                                borderRadius: '0.75rem',
                                background: s.session_id === sessionId ? 'rgba(147, 51, 234, 0.15)' : 'rgba(255,255,255,0.02)',
                                border: '1px solid',
                                borderColor: s.session_id === sessionId ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                fontSize: '0.85rem',
                                position: 'relative'
                            }}
                            className="session-item"
                            onClick={() => fetchMessages(s.session_id)}
                        >
                            {editingSessionId === s.session_id ? (
                                <div style={{ display: 'flex', gap: '0.25rem' }}>
                                    <input
                                        autoFocus
                                        value={editTitle}
                                        onChange={(e) => setEditTitle(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                        style={{ fontSize: '0.8rem', padding: '0.2rem', background: 'transparent', color: 'white', border: 'none', borderBottom: '1px solid var(--primary)', width: '100%' }}
                                    />
                                    <Check size={14} onClick={(e) => { e.stopPropagation(); handleRename(s.session_id); }} style={{ color: '#22c55e' }} />
                                    <X size={14} onClick={(e) => { e.stopPropagation(); setEditingSessionId(null); }} style={{ color: '#ef4444' }} />
                                </div>
                            ) : (
                                <>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <div style={{ fontWeight: '600', marginBottom: '0.25rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', width: '70%' }}>
                                            {s.title || "New Chat"}
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.5rem', opacity: 0.6 }}>
                                            <Pencil
                                                size={12}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setEditingSessionId(s.session_id);
                                                    setEditTitle(s.title);
                                                }}
                                            />
                                            <Trash2
                                                size={12}
                                                onClick={(e) => handleDeleteSession(e, s.session_id)}
                                                style={{ color: '#ef4444' }}
                                            />
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>
                                        {new Date(s.last_updated).toLocaleDateString()}
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                    {sessions.length === 0 && (
                        <p style={{ fontSize: '0.8rem', opacity: 0.5, textAlign: 'center', marginTop: '1rem' }}>No past chats</p>
                    )}
                </div>
            </div>

            {/* Sidebar Toggle Button */}
            <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                style={{
                    position: 'absolute',
                    left: isSidebarOpen ? '265px' : '-10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 10,
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
                    transition: 'all 0.3s ease'
                }}
            >
                {isSidebarOpen ? <ChevronLeft size={16} color="white" /> : <ChevronRight size={16} color="white" />}
            </button>

            {/* Main Chat Area */}
            <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem', overflow: 'hidden' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ background: 'var(--primary)', padding: '0.5rem', borderRadius: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 10px rgba(147, 51, 234, 0.3)' }}>
                            <Bot size={20} color="white" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>AI Analysis</h2>
                        </div>
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1.5rem', paddingRight: '0.5rem' }}>
                    {messages.length === 0 && (
                        <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--text-muted)' }}>
                            <Bot size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                            <p style={{ fontSize: '0.9rem' }}>Select a previous chat or start a fresh one.<br />I have access to all scores and feedback logs.</p>
                        </div>
                    )}
                    {messages.map((m, i) => (
                        <div key={i} className={`chat-bubble ${m.role}`}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', opacity: 0.7 }}>
                                {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                                <span style={{ fontSize: '0.7rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{m.role === 'user' ? 'Manager' : 'Assistant'}</span>
                            </div>
                            <div style={{ fontSize: '0.9375rem', fontWeight: '400', lineHeight: '1.6' }}>
                                {m.role === 'ai' ? (
                                    <div className="markdown-body">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {m.text}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    m.text
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="chat-bubble ai pulse" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div className="loading-dots">Analysing performance data...</div>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '1rem', border: '1px solid var(--border)' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type a query..."
                        style={{ border: 'none', background: 'transparent', boxShadow: 'none', flex: 1, color: 'white' }}
                    />
                    <button className="btn" onClick={handleSend} disabled={loading} style={{ borderRadius: '0.75rem', padding: '0.5rem 1rem' }}>
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatBot;
