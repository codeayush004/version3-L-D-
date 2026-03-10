import React, { useMemo, useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Award, AlertCircle } from 'lucide-react';

interface Intern {
    EmpID: string;
    Name: string;
    Email: string;
    [key: string]: any;
}

interface Subject {
    name: string;
    total_marks: number;
}

interface Props {
    data: Intern[];
    subjects: Subject[];
    managerId: string;
    batchId: string;
}

const BatchDashboard: React.FC<Props> = ({ data, subjects, managerId, batchId }) => {
    const [settings, setSettings] = useState<any>(null);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await axios.get(`http://localhost:5000/api/settings?manager_id=${managerId}&batch_id=${batchId}`);
                setSettings(res.data);
            } catch (error) {
                console.error("Failed to fetch settings", error);
            }
        };
        fetchSettings();
    }, [managerId, batchId]);

    const stats = useMemo(() => {
        if (data.length === 0 || subjects.length === 0) return null;

        const internAverages = data.map(intern => {
            let finalScore = 0;

            if (settings?.weightages) {
                subjects.forEach(sub => {
                    const score = intern[sub.name] || 0;
                    const weight = settings.weightages[sub.name];
                    if (weight) {
                        finalScore += (score / sub.total_marks) * weight;
                    }
                });

                // If weightages are used but don't add up to 100, we still return finalScore
                // finalScore is already out of 100 max if weights sum to 100.
            } else {
                let totalS = 0; let totalM = 0;
                subjects.forEach(sub => {
                    totalS += intern[sub.name] || 0;
                    totalM += sub.total_marks;
                });
                finalScore = totalM > 0 ? (totalS / totalM) * 100 : 0;
            }

            const avg = finalScore;
            return { ...intern, average: avg };
        });

        const batchAverage = internAverages.length > 0
            ? internAverages.reduce((acc, curr) => acc + curr.average, 0) / internAverages.length
            : 0;

        const topPerformers = [...internAverages]
            .sort((a, b) => b.average - a.average)
            .slice(0, 5);

        const subjectStats = subjects.map(sub => {
            const totalScore = data.reduce((acc, intern) => acc + (intern[sub.name] || 0), 0);
            const avg = (totalScore / (data.length * sub.total_marks)) * 100;
            return { name: sub.name, average: avg };
        });

        const threshold = settings?.passing_score || 60;
        const needsAttention = internAverages
            .filter(intern => intern.average < threshold)
            .sort((a, b) => a.average - b.average);

        return {
            batchAverage: batchAverage.toFixed(1),
            topPerformers,
            subjectStats,
            needsAttention,
            totalInterns: data.length,
            totalSubjects: subjects.length,
            threshold
        };
    }, [data, subjects, settings]);

    if (!stats) {
        return (
            <div className="card" style={{ textAlign: 'center', padding: '4rem', background: 'rgba(255,255,255,0.02)', borderStyle: 'dashed' }}>
                <AlertCircle size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem', opacity: 0.5 }} />
                <h3 style={{ fontSize: '1.25rem', fontWeight: '600' }}>Waiting for Data</h3>
                <p style={{ color: 'var(--text-muted)' }}>Upload an Excel sheet or specify course scores to see the batch analysis.</p>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
                <div className="card" style={{ background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.15), rgba(30, 41, 59, 0))' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--primary)', marginBottom: '1rem' }}>
                        <TrendingUp size={20} />
                        <span style={{ fontSize: '0.75rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Batch Average</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                        <h3 style={{ fontSize: '3rem', fontWeight: '900', color: 'white', lineHeight: '1' }}>{stats.batchAverage}</h3>
                        <span style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--primary)' }}>%</span>
                    </div>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '1rem' }}>Overall Performance</p>
                </div>


            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <div className="card" style={{ background: 'rgba(255,255,255,0.02)', margin: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                        <Award size={20} style={{ color: '#fbbf24' }} />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Top Ranked</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {stats.topPerformers.map((intern, idx) => (
                            <div key={intern.EmpID} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', border: '1px solid var(--border)' }}>
                                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: idx === 0 ? 'rgba(251, 191, 36, 0.1)' : 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', color: idx === 0 ? '#fbbf24' : 'var(--text-muted)' }}>
                                    #{idx + 1}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <p style={{ fontWeight: '600', color: 'white', fontSize: '0.9rem' }}>{intern.Name}</p>
                                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{intern.EmpID}</p>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <p style={{ fontWeight: '800', color: 'var(--primary)' }}>{intern.average.toFixed(1)}%</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="card" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', margin: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                        <AlertCircle size={20} style={{ color: '#ef4444' }} />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Needs Attention</h3>
                        <span style={{ marginLeft: 'auto', background: '#ef4444', color: 'white', fontSize: '0.7rem', padding: '0.1rem 0.5rem', borderRadius: '1rem', fontWeight: '800' }}>{stats.needsAttention.length}</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {stats.needsAttention.length > 0 ? (
                            stats.needsAttention.slice(0, 5).map(intern => (
                                <div key={intern.EmpID} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.05)', borderRadius: '0.75rem', border: '1px solid rgba(239, 68, 68, 0.1)' }}>
                                    <div style={{ flex: 1 }}>
                                        <p style={{ fontWeight: '600', color: 'white', fontSize: '0.9rem' }}>{intern.Name}</p>
                                        <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)' }}>{intern.EmpID}</p>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <p style={{ fontWeight: '800', color: '#ef4444' }}>{intern.average.toFixed(1)}%</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                All interns are performing above {stats.threshold}% passing score.
                            </div>
                        )}
                    </div>
                </div>
            </div>


        </div>
    );
};

export default BatchDashboard;
