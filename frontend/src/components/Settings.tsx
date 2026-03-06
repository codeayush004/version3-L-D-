import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, RefreshCw, ShieldCheck, Percent } from 'lucide-react';

interface SettingsProps {
    managerId: string;
    batchId: string;
}

const Settings: React.FC<SettingsProps> = ({ managerId, batchId }) => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<any>({
        passing_score: 60,
        recommended_score: 85,
        borderline_score: 65,
        weightages: {}
    });

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await axios.get(`http://localhost:5000/api/settings?manager_id=${managerId}&batch_id=${batchId}`);
                setSettings(res.data);
            } catch (error) {
                console.error("Failed to fetch settings", error);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, [managerId, batchId]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await axios.post('http://localhost:5000/api/settings', {
                ...settings,
                manager_id: managerId,
                batch_id: batchId
            });
            alert("Settings saved successfully!");
        } catch (error) {
            console.error("Failed to save settings", error);
            alert("Failed to save settings");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="card glass" style={{ textAlign: 'center', padding: '4rem' }}><div className="spinner"></div></div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(30, 41, 59, 0) 100%)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'var(--primary)', padding: '0.75rem', borderRadius: '1rem', color: 'white' }}>
                        <ShieldCheck size={24} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: '800' }}>Threshold Configuration</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Set performance limits and scoring weightages for automated analysis</p>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem' }}>
                <div className="card">
                    <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem', fontWeight: '700' }}>
                        <ShieldCheck size={20} className="text-secondary" /> Recommendation Thresholds
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <div className="input-group">
                            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Highly Recommended (FTE)</span>
                                <span style={{ color: 'var(--secondary)', fontWeight: '700' }}>{settings.recommended_score}%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="100"
                                value={settings.recommended_score}
                                onChange={(e) => setSettings({ ...settings, recommended_score: parseInt(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>

                        <div className="input-group" style={{ opacity: 0.8, background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '0.75rem', border: '1px dashed var(--border)' }}>
                            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span>Borderline Zone (Auto-Calculated)</span>
                                <span style={{ color: '#fbbf24', fontWeight: '700' }}>{settings.passing_score + 1}% - {Math.max(settings.passing_score + 1, settings.recommended_score - 1)}%</span>
                            </label>
                            <div style={{ width: '100%', height: '8px', background: 'linear-gradient(90deg, #ef4444 0%, #fbbf24 50%, #10b981 100%)', borderRadius: '4px', opacity: 0.5, marginTop: '0.5rem' }}></div>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.75rem', lineHeight: '1.4' }}>
                                Interns scoring strictly above the Redline and below the Recommended line are placed in the Yellow zone.
                            </p>
                        </div>

                        <div className="input-group">
                            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Passing Score (Redline)</span>
                                <span style={{ color: '#ef4444', fontWeight: '700' }}>{settings.passing_score}%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="100"
                                value={settings.passing_score}
                                onChange={(e) => setSettings({ ...settings, passing_score: parseInt(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>
                    </div>
                </div>

                <div className="card">
                    <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem', fontWeight: '700' }}>
                        <Percent size={20} className="text-primary" /> Scoring Weightage
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {Object.keys(settings.weightages).map(key => (
                            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '0.75rem', border: '1px solid var(--border)' }}>
                                <span style={{ flex: 1, fontSize: '0.9rem', fontWeight: '600' }}>{key}</span>
                                <input
                                    type="number"
                                    value={settings.weightages[key]}
                                    onChange={(e) => {
                                        const newWeightages = { ...settings.weightages, [key]: parseInt(e.target.value) || 0 };
                                        setSettings({ ...settings, weightages: newWeightages });
                                    }}
                                    style={{ width: '60px', padding: '0.4rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'transparent', color: 'white', textAlign: 'center' }}
                                />
                                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>%</span>
                            </div>
                        ))}
                    </div>

                    <div style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: '0.75rem', background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Total Configured</span>
                            <span style={{ fontSize: '1.2rem', fontWeight: '900', color: (Object.values(settings.weightages).reduce((a: any, b: any) => a + b, 0) as number) === 100 ? 'var(--secondary)' : '#ef4444' }}>
                                {(Object.values(settings.weightages).reduce((a: any, b: any) => a + b, 0) as number)}%
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button
                    className="btn"
                    style={{ background: 'transparent', border: '1px solid var(--border)' }}
                    onClick={() => window.location.reload()}
                >
                    <RefreshCw size={18} style={{ marginRight: '0.5rem' }} /> Discard
                </button>
                <button
                    className="btn"
                    onClick={handleSave}
                    disabled={saving}
                >
                    <Save size={18} style={{ marginRight: '0.5rem' }} /> {saving ? 'Saving...' : 'Apply Changes'}
                </button>
            </div>
        </div>
    );
};

export default Settings;
