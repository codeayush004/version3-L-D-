import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ClipboardList, RotateCcw } from 'lucide-react';
import InternDetail from './InternDetail';

interface Intern {
    EmpID: string;
    Name: string;
    Email: string;
    attempts: { [key: string]: string };
}

interface Props {
    managerId: string;
    batchId: string;
}

const AttemptTracker: React.FC<Props> = ({ managerId, batchId }) => {
    const [interns, setInterns] = useState<Intern[]>([]);
    const [subjects, setSubjects] = useState<{ name: string }[]>([]);
    const [selectedInternId, setSelectedInternId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [gridRes, subsRes] = await Promise.all([
                axios.get(`http://localhost:5000/api/attempts-grid?manager_id=${managerId}&batch_id=${batchId}`),
                axios.get(`http://localhost:5000/api/subjects?manager_id=${managerId}&batch_id=${batchId}`)
            ]);
            setInterns(gridRes.data);
            setSubjects(subsRes.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [managerId, batchId]);

    const handleUpdateAttempt = async (empId: string, subject: string, note: string) => {
        try {
            await axios.post('http://localhost:5000/api/update-attempt', {
                EmpID: empId,
                subject,
                attempt_note: note,
                manager_id: managerId,
                batch_id: batchId
            });
            // Update local state for responsiveness
            setInterns(prev => prev.map(i => {
                if (i.EmpID === empId) {
                    return { ...i, attempts: { ...i.attempts, [subject]: note } };
                }
                return i;
            }));
        } catch (error) {
            console.error(error);
        }
    };

    if (loading) return <div style={{ color: 'var(--text-muted)' }}>Loading Attempt Tracker...</div>;

    return (
        <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <ClipboardList size={24} className="text-secondary" /> Attempt & Retake Tracker
                    </h2>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Log and track re-attempts for each course module.</p>
                </div>
                <button className="btn" onClick={fetchData} style={{ padding: '0.6rem' }}>
                    <RotateCcw size={18} />
                </button>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Intern Name</th>
                            <th>Emp ID</th>
                            {subjects.map(s => (
                                <th key={s.name} style={{ minWidth: '180px' }}>
                                    {s.name}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {interns.map(intern => (
                            <tr key={intern.EmpID}>
                                <td
                                    style={{ fontWeight: '600', color: 'var(--primary)', cursor: 'pointer' }}
                                    onClick={() => setSelectedInternId(intern.EmpID)}
                                >
                                    {intern.Name}
                                </td>
                                <td style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>{intern.EmpID}</td>
                                {subjects.map(s => (
                                    <td key={s.name} style={{ padding: '0.5rem' }}>
                                        <select
                                            value={intern.attempts[s.name] || '1st Attempt'}
                                            onChange={(e) => handleUpdateAttempt(intern.EmpID, s.name, e.target.value)}
                                            style={{
                                                width: '100%',
                                                background: 'rgba(255,255,255,0.02)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '6px',
                                                padding: '0.4rem',
                                                color: intern.attempts[s.name] && intern.attempts[s.name] !== '1st Attempt' ? 'var(--secondary)' : '#fff',
                                                fontSize: '0.85rem',
                                                outline: 'none',
                                                fontWeight: intern.attempts[s.name] && intern.attempts[s.name] !== '1st Attempt' ? '700' : '400'
                                            } as any}
                                        >
                                            <option value="1st Attempt">1st Attempt</option>
                                            <option value="2nd Attempt">2nd Attempt</option>
                                            <option value="3rd Attempt">3rd Attempt</option>
                                            <option value="Failed">Failed</option>
                                        </select>
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
                {interns.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        No intern data available to track attempts.
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

export default AttemptTracker;
