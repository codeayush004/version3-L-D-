import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare } from 'lucide-react';
import InternDetail from './InternDetail';

interface Intern {
    EmpID: string;
    Name: string;
    Email: string;
    [key: string]: any;
}

interface Props {
    data: Intern[];
    managerId: string;
    batchId: string;
}

const InternGrid: React.FC<Props> = ({ data, managerId, batchId }) => {
    const [selectedInternId, setSelectedInternId] = useState<string | null>(null);
    const [subjects, setSubjects] = useState<{ name: string, total_marks: number }[]>([]);
    const [settings, setSettings] = useState<any>(null);



    useEffect(() => {
        const fetchSubjectsAndSettings = async () => {
            try {
                const [subjRes, settingsRes] = await Promise.all([
                    axios.get(`http://localhost:5000/api/subjects?manager_id=${managerId}&batch_id=${batchId}`),
                    axios.get(`http://localhost:5000/api/settings?manager_id=${managerId}&batch_id=${batchId}`)
                ]);
                setSubjects(subjRes.data);
                setSettings(settingsRes.data);
            } catch (error) {
                console.error(error);
            }
        };
        fetchSubjectsAndSettings();
    }, [data, managerId, batchId]);





    const showInternDetail = (empId: string) => {
        setSelectedInternId(empId);
    };

    return (
        <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Grade Sheet</h2>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>View and manage scores for all subjects.</p>
                </div>

                <div></div>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Intern Name</th>
                            <th>INT ID</th>
                            {subjects.map(s => (
                                <th key={s.name}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ color: 'var(--primary)' }}>{s.name}</div>
                                            <div style={{ fontSize: '0.6rem', opacity: 0.6 }}>Total: {s.total_marks}</div>
                                        </div>

                                    </div>
                                </th>
                            ))}
                            <th>Final Score</th>
                            <th>Feedback</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map(intern => (
                            <tr key={intern.EmpID} onClick={() => showInternDetail(intern.EmpID)} style={{ cursor: 'pointer' }}>
                                <td style={{ fontWeight: '600', color: 'var(--primary)' }}>{intern.Name}</td>
                                <td style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>{intern.EmpID}</td>
                                {subjects.map(s => {
                                    const score = (intern as any)[s.name] || 0;
                                    const weight = settings?.weightages?.[s.name];
                                    const contribution = weight ? ((score / s.total_marks) * weight).toFixed(1) : null;

                                    return (
                                        <td key={s.name} onClick={e => e.stopPropagation()}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <span style={{ fontWeight: '700', fontSize: '1.1rem', color: 'white' }}>{score}</span>
                                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/ {s.total_marks}</span>
                                                </div>
                                                {contribution !== null && (
                                                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '600', opacity: 0.8 }}>
                                                        +{contribution}% overall
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                    );
                                })}
                                {(() => {
                                    let finalScore = 0;
                                    let oldStyleTotalS = 0;
                                    let oldStyleTotalM = 0;

                                    subjects.forEach(s => {
                                        const score = (intern as any)[s.name] || 0;
                                        const weight = settings?.weightages?.[s.name];
                                        if (weight) {
                                            finalScore += (score / s.total_marks) * weight;
                                        } else {
                                            oldStyleTotalS += score;
                                            oldStyleTotalM += s.total_marks;
                                        }
                                    });

                                    let averagePerformance = 0;
                                    if (settings && Object.keys(settings.weightages || {}).length > 0) {
                                        averagePerformance = parseFloat(finalScore.toFixed(1));
                                    } else {
                                        averagePerformance = oldStyleTotalM > 0
                                            ? parseFloat(((oldStyleTotalS / oldStyleTotalM) * 100).toFixed(1))
                                            : 0;
                                    }

                                    let scoreColor = 'white';
                                    if (settings) {
                                        if (averagePerformance >= settings.recommended_score) scoreColor = '#10b981'; // Green
                                        else if (averagePerformance > settings.passing_score) scoreColor = '#fbbf24'; // Yellow
                                        else scoreColor = '#ef4444'; // Red
                                    }

                                    return (
                                        <td>
                                            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: scoreColor }}>
                                                {averagePerformance}%
                                            </div>
                                        </td>
                                    );
                                })()}
                                <td style={{ maxWidth: '300px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                        <MessageSquare size={14} style={{ flexShrink: 0 }} />
                                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {(intern as any).latest_feedback || 'No feedback yet'}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {data.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        No intern data available. Import an Excel sheet to populate the grade sheet.
                    </div>
                )}
            </div>

            {selectedInternId && (
                <InternDetail
                    empId={selectedInternId}
                    managerId={managerId}
                    batchId={batchId}
                    onClose={() => setSelectedInternId(null)}
                />
            )}
        </div>
    );
};

export default InternGrid;
