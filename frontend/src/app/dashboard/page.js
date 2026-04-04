"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, removeToken } from "@/lib/api";
import Link from "next/link";

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [balances, setBalances] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newGroupName, setNewGroupName] = useState("");
  const [creatingGroup, setCreatingGroup] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [userData, balanceData, groupData] = await Promise.all([
        api.getMe(),
        api.getMyBalances(),
        api.getGroups()
      ]);
      setUser(userData);
      setBalances(balanceData);
      setGroups(groupData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    removeToken();
    router.push("/");
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    
    setCreatingGroup(true);
    try {
      await api.createGroup(newGroupName);
      setNewGroupName("");
      // Refresh groups
      const groupData = await api.getGroups();
      setGroups(groupData);
    } catch (err) {
      alert(err.message || "Failed to create group");
    } finally {
      setCreatingGroup(false);
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'white' }}>Loading dashboard...</div>;
  }

  // Calculate generic total formatting
  const totalOwed = balances.filter(b => b.user_id === user?.id).reduce((acc, curr) => acc + curr.amount, 0);
  const totalOwedToMe = balances.filter(b => b.owes_to_id === user?.id).reduce((acc, curr) => acc + curr.amount, 0);

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem 1rem' }}>
      
      {/* Header Profile Area */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold' }}>Dashboard</h1>
          <p style={{ color: '#94a3b8' }}>Welcome back, {user?.full_name}</p>
        </div>
        <button onClick={handleLogout} className="btn danger" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
          Logout
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        
        {/* Balances Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#60a5fa' }}>Overall Balances</h2>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8' }}>You Owe</span>
              <span style={{ color: '#ef4444', fontWeight: 'semibold' }}>${totalOwed.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>You are owed</span>
              <span style={{ color: '#10b981', fontWeight: 'semibold' }}>${totalOwedToMe.toFixed(2)}</span>
            </div>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Settle Up Needs</h2>
            {balances.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>You are all settled up!</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {balances.map(b => {
                  const amIOwed = b.owes_to_id === user?.id;
                  const otherParam = amIOwed ? b.user : b.owes_to;
                  const otherName = otherParam?.full_name || otherParam?.email || `User #${amIOwed ? b.user_id : b.owes_to_id}`;
                  
                  return (
                    <li key={b.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <span>{otherName}</span>
                      <span style={{ color: amIOwed ? '#10b981' : '#ef4444', fontWeight: '500' }}>
                        {amIOwed ? `Owes you $${b.amount.toFixed(2)}` : `You owe $${b.amount.toFixed(2)}`}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        {/* Groups Column */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', color: '#34d399' }}>Your Groups</h2>
          
          <div style={{ flex: 1 }}>
            {groups.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '2rem' }}>You are not part of any groups yet.</p>
            ) : (
              <div style={{ display: 'grid', gap: '1rem', marginBottom: '2rem' }}>
                {groups.map(group => (
                  <Link href={`/groups/${group.id}`} key={group.id} style={{ display: 'block', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s ease' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>{group.name}</h3>
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>View details & expenses →</p>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={handleCreateGroup} style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Create New Group</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                className="input-field"
                style={{ marginBottom: 0, flex: 1 }}
                placeholder="Trip to Paris..."
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                required
              />
              <button type="submit" className="btn" disabled={creatingGroup}>
                {creatingGroup ? "+++" : "Create"}
              </button>
            </div>
          </form>

        </div>

      </div>
    </div>
  );
}
