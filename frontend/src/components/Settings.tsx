import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, RefreshCw } from 'lucide-react';

interface SettingsProps {
    managerId: string;
    batchId: string;
}

const Settings: React.FC<SettingsProps> = ({ managerId, batchId }) => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<any>({
        passing_score: 60,
        recommended_score: 75,
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
            <div style={{ padding: '0.5rem 0' }}>
                <h2 style={{ fontSize: '1.75rem', fontWeight: '900', letterSpacing: '-0.02em' }}>Grading Rules</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem' }}>
                <div className="card">
                    <h3 style={{ marginBottom: '2rem', fontSize: '1rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                        Performance Levels
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        {/* Green Zone */}
                        <div className="input-group" style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '1.25rem', borderRadius: '1rem', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                <span style={{ color: '#10b981', fontWeight: '800', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Green Zone (Highly Recommended)</span>
                                <span style={{ color: '#10b981', fontWeight: '800', fontSize: '1.1rem' }}>{settings.recommended_score}% - 100%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="100"
                                value={settings.recommended_score}
                                onChange={(e) => setSettings({ ...settings, recommended_score: parseInt(e.target.value) })}
                                style={{ width: '100%', accentColor: '#10b981', cursor: 'pointer' }}
                            />
                        </div>

                        {/* Yellow Zone */}
                        <div style={{ textAlign: 'center', padding: '0.5rem', background: 'rgba(251, 191, 36, 0.1)', borderRadius: '0.75rem', border: '1px dashed rgba(251, 191, 36, 0.3)' }}>
                            <span style={{ color: '#fbbf24', fontWeight: '800', textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.1em' }}>Yellow Zone (Borderline)</span>
                            <div style={{ fontSize: '0.9rem', fontWeight: '700', color: 'white', marginTop: '0.25rem' }}>
                                {settings.passing_score + 1}% - {settings.recommended_score - 1}%
                            </div>
                        </div>

                        {/* Red Zone */}
                        <div className="input-group" style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '1.25rem', borderRadius: '1rem', border: '1px solid rgba(239, 68, 68, 0.1)' }}>
                            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                <span style={{ color: '#ef4444', fontWeight: '800', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Red Zone (Needs Attention)</span>
                                <span style={{ color: '#ef4444', fontWeight: '800', fontSize: '1.1rem' }}>0% - {settings.passing_score}%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="100"
                                value={settings.passing_score}
                                onChange={(e) => setSettings({ ...settings, passing_score: parseInt(e.target.value) })}
                                style={{ width: '100%', accentColor: '#ef4444', cursor: 'grab' }}
                            />
                        </div>

                        <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textAlign: 'center', opacity: 0.6 }}>
                            * Adjust sliders to define boundaries for automated recommendations.
                        </p>
                    </div>
                </div>

                <div className="card">
                    <h3 style={{ marginBottom: '2rem', fontSize: '1rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                        Subject Weights
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {Object.keys(settings.weightages).map(key => (
                            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '0.75rem', border: '1px solid var(--border)' }}>
                                <span style={{ flex: 1, fontSize: '0.9rem', fontWeight: '600' }}>{key}</span>
                                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                                    <input
                                        type="number"
                                        value={settings.weightages[key]}
                                        onChange={(e) => {
                                            const newWeightages = { ...settings.weightages, [key]: parseInt(e.target.value) || 0 };
                                            setSettings({ ...settings, weightages: newWeightages });
                                        }}
                                        style={{ width: '70px', padding: '0.4rem 1.4rem 0.4rem 0.5rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'transparent', color: 'white', textAlign: 'center' }}
                                    />
                                    <span style={{ position: 'absolute', right: '0.6rem', color: 'var(--text-muted)', fontSize: '0.75rem', pointerEvents: 'none' }}>%</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: '0.75rem', background: 'rgba(147, 51, 234, 0.05)', border: '1px solid rgba(147, 51, 234, 0.1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Total Weightage</span>
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
                    <Save size={18} style={{ marginRight: '0.5rem' }} /> {saving ? 'Saving...' : 'Save'}
                </button>
            </div>
        </div >
    );
};

export default Settings;
