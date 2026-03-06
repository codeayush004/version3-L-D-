import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Users, Target, Activity, Award } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
    managerId: string;
    activeDepartment: string;
}

const GlobalDashboard: React.FC<Props> = ({ managerId, activeDepartment }) => {
    const [loading, setLoading] = useState(true);
    const [globalStats, setGlobalStats] = useState<any>(null);

    useEffect(() => {
        const fetchAllData = async () => {
            try {
                const batchRes = await axios.get(`http://localhost:5000/api/batches?manager_id=${managerId}&department=${activeDepartment}`);
                const batchList = batchRes.data;

                // 2. Fetch scores, settings, and subjects for EVERY batch
                let totalInterns = 0;
                let orgTotalScore = 0;
                let orgTotalCount = 0;
                const batchAverages = [];
                const allInterns: any[] = [];

                for (const b of batchList) {
                    const [scoresRes, settingsRes, subjectsRes] = await Promise.all([
                        axios.get(`http://localhost:5000/api/scores?manager_id=${managerId}&batch_id=${b.batch_id}`),
                        axios.get(`http://localhost:5000/api/settings?manager_id=${managerId}&batch_id=${b.batch_id}`),
                        axios.get(`http://localhost:5000/api/subjects?manager_id=${managerId}&batch_id=${b.batch_id}`)
                    ]);

                    const data = scoresRes.data;
                    const settings = settingsRes.data;
                    const subjects = subjectsRes.data;

                    totalInterns += data.length;

                    // Calculate batch average just like in BatchDashboard
                    let batchSum = 0;
                    data.forEach((intern: any) => {
                        let finalScore = 0;
                        if (settings?.weightages && Object.keys(settings.weightages).length > 0) {
                            subjects.forEach((sub: any) => {
                                const score = intern[sub.name] || 0;
                                const weight = settings.weightages[sub.name];
                                if (weight) {
                                    finalScore += (score / sub.total_marks) * weight;
                                }
                            });
                        } else {
                            let totalS = 0; let totalM = 0;
                            subjects.forEach((sub: any) => {
                                totalS += intern[sub.name] || 0;
                                totalM += sub.total_marks;
                            });
                            finalScore = totalM > 0 ? (totalS / totalM) * 100 : 0;
                        }

                        allInterns.push({
                            ...intern,
                            average: finalScore,
                            batchName: b.name
                        });

                        batchSum += finalScore;
                        orgTotalScore += finalScore;
                        orgTotalCount++;
                    });

                    const batchAvg = data.length > 0 ? batchSum / data.length : 0;
                    batchAverages.push({
                        name: b.name,
                        average: parseFloat(batchAvg.toFixed(1)),
                        interns: data.length
                    });
                }

                setGlobalStats({
                    totalInterns,
                    totalBatches: batchList.length,
                    overallAverage: orgTotalCount > 0 ? (orgTotalScore / orgTotalCount).toFixed(1) : '0.0',
                    batchAverages: batchAverages.sort((a, b) => b.average - a.average),
                    topPerformers: allInterns.sort((a, b) => b.average - a.average).slice(0, 5)
                });
            } catch (error) {
                console.error("Global fetch failed", error);
            } finally {
                setLoading(false);
            }
        };

        if (managerId) fetchAllData();
    }, [managerId, activeDepartment]);

    if (loading) return <div className="card glass" style={{ textAlign: 'center', padding: '4rem' }}><div className="spinner"></div></div>;
    if (!globalStats || globalStats.totalBatches === 0) return (
        <div className="card" style={{ textAlign: 'center', padding: '4rem', background: 'rgba(255,255,255,0.02)', borderStyle: 'dashed' }}>
            <Activity size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem', opacity: 0.5 }} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600' }}>No Active Workspaces</h3>
            <p style={{ color: 'var(--text-muted)' }}>Create your first batch to start tracking organizational metrics.</p>
        </div>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(30, 41, 59, 0) 100%)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'var(--primary)', padding: '0.75rem', borderRadius: '1rem', color: 'white' }}>
                        <TrendingUp size={24} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: '800' }}>Global L&D Overview</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Aggregate performance metrics across all your active batches and workspaces</p>
                    </div>
                </div>
            </div>

            <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--primary)', marginBottom: '1rem' }}>
                        <Activity size={20} />
                        <span style={{ fontSize: '0.75rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Organization Avg</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                        <h3 style={{ fontSize: '3rem', fontWeight: '900', color: 'white', lineHeight: '1' }}>{globalStats.overallAverage}</h3>
                        <span style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--primary)' }}>%</span>
                    </div>
                </div>

                <div className="card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--secondary)', marginBottom: '1rem' }}>
                        <Users size={20} />
                        <span style={{ fontSize: '0.75rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Total Interns</span>
                    </div>
                    <h3 style={{ fontSize: '3rem', fontWeight: '900', color: 'white', lineHeight: '1' }}>{globalStats.totalInterns}</h3>
                </div>

                <div className="card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fbbf24', marginBottom: '1rem' }}>
                        <Target size={20} />
                        <span style={{ fontSize: '0.75rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Active Batches</span>
                    </div>
                    <h3 style={{ fontSize: '3rem', fontWeight: '900', color: 'white', lineHeight: '1' }}>{globalStats.totalBatches}</h3>
                </div>
            </div>

            <div className="card" style={{ padding: '2rem' }}>
                <h3 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem', fontWeight: '700' }}>
                    <Award size={20} className="text-secondary" /> Batch Comparison Matrix
                </h3>
                <div style={{ width: '100%', height: '350px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={globalStats.batchAverages}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                            <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} />
                            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} domain={[0, 100]} />
                            <Tooltip
                                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                                contentStyle={{ background: '#1e293b', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                            />
                            <Bar dataKey="average" fill="var(--primary)" radius={[4, 4, 0, 0]} barSize={45} name="Batch Average (%)" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="card" style={{ background: 'rgba(255,255,255,0.02)', margin: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                    <Award size={20} style={{ color: '#fbbf24' }} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Organization's Elite Performers</h3>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                    {globalStats.topPerformers.map((intern: any, idx: number) => (
                        <div key={`${intern.EmpID}-${idx}`} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', border: '1px solid var(--border)' }}>
                            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: idx === 0 ? 'rgba(251, 191, 36, 0.1)' : 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', color: idx === 0 ? '#fbbf24' : 'var(--text-muted)' }}>
                                #{idx + 1}
                            </div>
                            <div style={{ flex: 1 }}>
                                <p style={{ fontWeight: '700', color: 'white', fontSize: '1rem', marginBottom: '0.2rem' }}>{intern.Name}</p>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{intern.EmpID} • <span style={{ color: 'var(--secondary)' }}>{intern.batchName}</span></p>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <p style={{ fontWeight: '900', color: 'var(--primary)', fontSize: '1.1rem' }}>{intern.average.toFixed(1)}%</p>
                            </div>
                        </div>
                    ))}
                    {globalStats.topPerformers.length === 0 && (
                        <p style={{ color: 'var(--text-muted)' }}>No interns found across any active batches.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GlobalDashboard;
