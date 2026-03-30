import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { createPortal } from 'react-dom';
import {
    X,
    Mail,
    Hash,
    TrendingUp,
    Award,
    Sparkles,
    Calendar,
    User,
    Activity,
    Target,
    Layers
} from 'lucide-react';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip
} from 'recharts';
import { API_BASE_URL } from '../config';
interface InternDetailProps {
    empId: string;
    managerId: string;
    batchId: string;
    onClose: () => void;
}

const InternDetail: React.FC<InternDetailProps> = ({ empId, managerId, batchId, onClose }) => {
    const [data, setData] = useState<any>(null);
    const [settings, setSettings] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [reportRes, settingsRes] = await Promise.all([
                    axios.get(`${API_BASE_URL}/api/reports/${empId}?manager_id=${managerId}&batch_id=${batchId}`),
                    axios.get(`${API_BASE_URL}/api/settings?manager_id=${managerId}&batch_id=${batchId}`)
                ]);
                setData(reportRes.data);
                setSettings(settingsRes.data);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [empId, managerId, batchId]);

    if (loading) return (
        <div className="modal-overlay">
            <div className="card glass" style={{ padding: '4rem', textAlign: 'center' }}>
                <div className="spinner"></div>
                <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Generating intern profile...</p>
            </div>
        </div>
    );

    if (!data) return null;

    const { intern, scores, subjects, rank, total_interns } = data;

    let finalScore = 0;
    let oldStyleTotalS = 0;
    let oldStyleTotalM = 0;

    const chartData = subjects.map((s: any) => {
        const sName = typeof s === 'string' ? s : s.name;
        const sTotal = typeof s === 'string' ? 100 : s.total_marks;
        const sScore = scores[sName] || 0;

        const percentage = (sScore / sTotal) * 100;

        if (settings?.weightages) {
            const weight = settings.weightages[sName];
            if (weight) {
                finalScore += (sScore / sTotal) * weight;
            }
        } else {
            oldStyleTotalS += sScore;
            oldStyleTotalM += sTotal;
        }

        return {
            subject: sName,
            score: sScore,
            total: sTotal,
            fullMark: sTotal,
            percentage: Math.round(percentage)
        };
    });

    let averagePerformance = 0;
    if (settings?.weightages) {
        averagePerformance = parseFloat(finalScore.toFixed(1));
    } else {
        averagePerformance = oldStyleTotalM > 0
            ? parseFloat(((oldStyleTotalS / oldStyleTotalM) * 100).toFixed(1))
            : 0;
    }

    const getRAGColor = (score: number) => {
        if (!settings) return '#6366f1';
        if (score >= settings.recommended_score) return '#10b981'; // Green
        if (score > settings.passing_score) return '#f59e0b'; // Amber (between passing and recommended)
        return '#ef4444'; // Red (below or equal to passing redline)
    };

    const getRAGLabel = (score: number) => {
        if (!settings) return 'Analyzing...';
        if (score >= settings.recommended_score) return 'Highly Recommended for FTE Conversion';
        if (score > settings.passing_score) return 'Borderline / Potential with Mentorship';
        return 'Needs Improvement';
    };

    const ragColor = getRAGColor(averagePerformance);
    const ragLabel = getRAGLabel(averagePerformance);


    return createPortal(
        <div id="dashboard-portal-root" className="modal-overlay" style={{
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
            overflowY: 'auto',
            zIndex: 9999,
            position: 'fixed',
            inset: 0,
            background: 'rgba(4, 7, 18, 0.9)',
            backdropFilter: 'blur(8px)'
        }}>
            <div className="modal-content" style={{
                maxWidth: '1200px',
                width: '90vw',
                height: '85vh',
                padding: 0,
                overflow: 'hidden',
                background: '#0f172a',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 40px 80px -15px rgba(0,0,0,0.8)',
                borderRadius: '1.5rem',
                border: '1px solid var(--border)'
            }}>
                {/* Header Section - Premium Layout */}
                <div style={{ background: 'linear-gradient(135deg, var(--primary) 0%, #581c87 100%)', padding: '2.5rem 6rem 2.5rem 2.5rem', position: 'relative', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                    <button
                        onClick={onClose}
                        style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', padding: '0.6rem', borderRadius: '50%', cursor: 'pointer', transition: 'all 0.3s', backdropFilter: 'blur(8px)' }}
                        onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                        onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                    >
                        <X size={20} />
                    </button>

                    <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
                        {/* Avatar */}
                        <div style={{ width: '70px', height: '70px', borderRadius: '1.25rem', background: 'linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.05) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.2rem', fontWeight: '800', color: 'white', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.3)', boxShadow: '0 10px 25px rgba(0,0,0,0.2)' }}>
                            {intern.Name.charAt(0)}
                        </div>

                        {/* Identification */}
                        <div>
                            <h1 style={{ fontSize: '2rem', fontWeight: '900', color: 'white', marginBottom: '0.2rem', letterSpacing: '-0.02em', textShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>{intern.Name}</h1>
                            <div style={{ display: 'flex', gap: '1.5rem', color: 'rgba(255,255,255,0.85)', fontSize: '0.85rem', fontWeight: '500' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Hash size={16} /> INT ID: {intern.EmpID}</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Mail size={16} /> {intern.Email}</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.6rem', color: 'rgba(255,255,255,0.9)', fontSize: '0.75rem', fontWeight: '600', marginTop: '0.6rem', flexWrap: 'wrap' }}>
                                {intern.mapped_batch && <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.15)', padding: '0.2rem 0.6rem', borderRadius: '2rem', border: '1px solid rgba(255,255,255,0.05)' }}><Layers size={12} /> {intern.mapped_batch}</span>}
                                {intern.date_of_joining && <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.15)', padding: '0.2rem 0.6rem', borderRadius: '2rem', border: '1px solid rgba(255,255,255,0.05)' }}><Calendar size={12} /> Joined: {intern.date_of_joining}</span>}
                                {intern.mentor_name && <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.15)', padding: '0.2rem 0.6rem', borderRadius: '2rem', border: '1px solid rgba(255,255,255,0.05)' }}><User size={12} /> Mentor: {intern.mentor_name}</span>}
                                {intern.training_status && <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.15)', padding: '0.2rem 0.6rem', borderRadius: '2rem', border: '1px solid rgba(255,255,255,0.05)' }}><Activity size={12} /> Status: {intern.training_status}</span>}
                                {intern.fte_conversion_date && <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.15)', padding: '0.2rem 0.6rem', borderRadius: '2rem', border: '1px solid rgba(255,255,255,0.05)' }}><Target size={12} /> FTE Date: {intern.fte_conversion_date}</span>}
                            </div>
                            <div style={{ display: 'flex', gap: '0.6rem', color: 'rgba(255,255,255,0.8)', fontSize: '0.7rem', fontWeight: '500', marginTop: '0.4rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.4rem' }}>
                                {intern.college && <span>🎓 {intern.college}</span>}
                                {intern.degree && <span>• {intern.degree}</span>}
                                {intern.cgpa && <span>• CGPA: {intern.cgpa}</span>}
                            </div>
                        </div>

                        {/* Metrics Block */}
                        <div style={{ marginLeft: 'auto', display: 'flex', gap: '2.5rem', alignItems: 'center', flexShrink: 0 }}>
                            {/* Cohort Rank */}
                            {rank && (
                                <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', borderRight: '1px solid rgba(255,255,255,0.2)', paddingRight: '2.5rem', whiteSpace: 'nowrap' }}>
                                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'rgba(255,255,255,0.7)', marginBottom: '0.25rem', fontWeight: '700' }}>Batch Rank</div>
                                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', whiteSpace: 'nowrap' }}>
                                        <span style={{ fontSize: '2.5rem', fontWeight: '900', color: '#38bdf8', lineHeight: '1', textShadow: '0 4px 15px rgba(56,189,248,0.4)' }}>#{rank}</span>
                                        <span style={{ fontSize: '1.1rem', color: 'rgba(255,255,255,0.6)', fontWeight: '700' }}>/ {total_interns}</span>
                                    </div>
                                </div>
                            )}

                            {/* Overall Score */}
                            <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'rgba(255,255,255,0.7)', marginBottom: '0.25rem', fontWeight: '700' }}>Overall Score</div>
                                <div style={{ fontSize: '3.2rem', fontWeight: '900', color: 'white', lineHeight: '1', textShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>{averagePerformance}%</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content Area - Scrollable */}
                <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem', flex: 1, overflowY: 'auto', background: 'rgba(15, 23, 42, 0.5)' }}>
                    {/* FTE Readiness Assessment Container - Full Width */}
                    <div className="card" style={{
                        background: `linear-gradient(135deg, ${ragColor}10 0%, rgba(30, 41, 59, 0) 100%)`,
                        border: `1px solid ${ragColor}30`,
                        margin: 0,
                        padding: '2rem 1.5rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        boxShadow: `0 10px 30px -10px ${ragColor}20`,
                        flexShrink: 0,
                        WebkitBoxAlign: 'center'
                    }}>
                        <div style={{ flex: 1, paddingRight: '2.5rem' }}>
                            <h3 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem', fontWeight: '700', color: 'white' }}>
                                <Award size={20} style={{ color: ragColor }} /> Performance
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '1.5rem 1rem' }}>
                                {subjects.map((s: any) => {
                                    const sName = typeof s === 'string' ? s : s.name;
                                    const sScore = scores[sName] || 0;
                                    return (
                                        <div key={sName} style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            padding: '0.85rem',
                                            borderRadius: '0.75rem',
                                            border: '1px solid rgba(255,255,255,0.05)',
                                            position: 'relative',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: '3px', background: ragColor, opacity: 0.5 }} />
                                            <p style={{ color: 'var(--text-muted)', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '0.25rem' }} title={sName}>{sName}</p>
                                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                                                <span style={{ fontSize: '1.25rem', fontWeight: '800', color: 'white', lineHeight: '1' }}>{sScore}</span>
                                                <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontWeight: '600' }}>/ 100</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        <div style={{ textAlign: 'right', minWidth: '180px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
                            <div style={{
                                background: `${ragColor}20`,
                                color: ragColor,
                                padding: '0.2rem 0.6rem',
                                borderRadius: '1rem',
                                fontSize: '0.65rem',
                                fontWeight: '800',
                                textTransform: 'uppercase',
                                marginBottom: '0.5rem',
                                border: `1px solid ${ragColor}40`,
                                display: 'inline-block'
                            }}>
                                {ragLabel}
                            </div>
                            <div style={{ fontSize: '2.5rem', fontWeight: '900', color: ragColor, lineHeight: '1' }}>{averagePerformance}%</div>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.25rem' }}>Final Grade</p>
                        </div>
                    </div>

                    <div className="card" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', margin: 0, padding: '2rem', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
                        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.2rem', fontWeight: '800' }}>
                            <TrendingUp size={24} className="text-primary" /> Skill Balance
                        </h3>
                        <div style={{ width: '100%', height: '400px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                                    <PolarGrid stroke="rgba(255,255,255,0.05)" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar
                                        name="Score"
                                        dataKey="percentage"
                                        stroke="var(--primary)"
                                        fill="var(--primary)"
                                        fillOpacity={0.6}
                                    />
                                    <Tooltip
                                        contentStyle={{ background: '#1e293b', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* AI Insights Section */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.05) 0%, rgba(30, 41, 59, 0) 100%)', border: '1px solid rgba(147, 51, 234, 0.2)', margin: 0, flexShrink: 0 }}>
                            <div style={{ padding: '1.5rem', background: 'rgba(147, 51, 234, 0.05)', borderRadius: '1rem', border: '1px solid rgba(147, 51, 234, 0.2)' }}>
                                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <Sparkles size={20} /> AI Insights
                                </h3>
                                <p style={{ color: 'white', fontSize: '0.95rem', lineHeight: '1.6', fontStyle: 'italic' }}>
                                    "{data.ai_summary}"
                                </p>
                            </div>
                        </div>

                        <div className="card" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', margin: 0 }}>
                            <div style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <Target size={20} className="text-primary" /> Mentor Remarks
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {data.feedbacks && data.feedbacks.length > 0 ? (
                                        data.feedbacks.map((f: any, idx: number) => (
                                            <div key={idx} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', borderLeft: '3px solid var(--primary)' }}>
                                                <p style={{ fontSize: '0.85rem', color: 'white' }}>{f.text}</p>
                                                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>- {f.column} ({f.date})</span>
                                            </div>
                                        ))
                                    ) : (
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No additional feedback recorded.</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div style={{ padding: '1rem 2rem', borderTop: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                    <button className="btn" onClick={onClose} style={{ background: 'transparent', border: '1px solid var(--border)', padding: '0.5rem 1.25rem', fontSize: '0.8rem' }}>
                        Return to Portal
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
};

export default InternDetail;
