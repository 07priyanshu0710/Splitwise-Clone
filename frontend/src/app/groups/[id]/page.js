"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";

export default function GroupDetail() {
  const { id } = useParams();
  const router = useRouter();

  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [memberIdentifier, setMemberIdentifier] = useState("");
  const [addingMember, setAddingMember] = useState(false);

  useEffect(() => {
    fetchGroupData();
  }, [id]);

  const fetchGroupData = async () => {
    try {
      const [grpData, expData] = await Promise.all([
        api.getGroup(id),
        api.getGroupExpenses(id)
      ]);
      setGroup(grpData);
      setExpenses(expData);
    } catch (err) {
      console.error(err);
      if (err.message === "Unauthorized") router.push("/");
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!memberIdentifier) return;

    setAddingMember(true);
    try {
      await api.addGroupMember(id, memberIdentifier);
      setMemberIdentifier("");
      const grpData = await api.getGroup(id);
      setGroup(grpData);
      alert('Member added successfully!');
    } catch (err) {
      alert(err.message || "Failed to add member");
    } finally {
      setAddingMember(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    if (!description || !amount) return;

    setSubmitting(true);
    try {
      await api.createExpense({
        description,
        amount: parseFloat(amount),
        group_id: parseInt(id),
        split_type: "equal",
        splits: group.members ? group.members.map(m => ({ user_id: m.user_id })) : []
      });

      setDescription("");
      setAmount("");
      const expData = await api.getGroupExpenses(id);
      setExpenses(expData);
    } catch (err) {
      alert(err.message || "Failed to create expense");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Loading group details...</p>
      </div>
    );
  }

  if (!group) return <div style={{ color: 'white', textAlign: 'center', marginTop: '5rem' }}>Group not found</div>;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>

      <div style={{ marginBottom: '2rem' }}>
        <Link href="/dashboard" style={{ color: '#60a5fa', fontSize: '0.875rem', marginBottom: '1rem', display: 'inline-block' }}>
          ← Back to Dashboard
        </Link>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold' }}>{group.name}</h1>
        <p style={{ color: '#94a3b8' }}>Group ID: {group.id}</p>
      </div>

      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#60a5fa' }}>Group Members</h2>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          {group.members.map((m) => (
            <span key={m.id} style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)', padding: '0.25rem 0.75rem', borderRadius: '999px', fontSize: '0.875rem' }}>
              👤 {m.user.full_name || m.user.email} <span style={{ opacity: 0.5 }}>({m.role})</span>
            </span>
          ))}
        </div>

        <form onSubmit={handleAddMember} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label className="label">Add Member (Email or Mobile)</label>
            <input
              type="text"
              className="input-field"
              placeholder="friend@example.com or +91 98765..."
              value={memberIdentifier}
              onChange={(e) => setMemberIdentifier(e.target.value)}
              style={{ marginBottom: 0 }}
              required
            />
          </div>
          <button type="submit" className="btn" disabled={addingMember}>
            {addingMember ? "Adding..." : "Add"}
          </button>
        </form>
      </div>

      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', color: '#10b981' }}>Add an Expense</h2>
        <form onSubmit={handleAddExpense} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px' }}>
            <label className="label">Description</label>
            <input
              type="text"
              className="input-field"
              placeholder="Dinner, taxi, groceries..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ marginBottom: 0 }}
              required
            />
          </div>
          <div style={{ flex: '0 0 150px' }}>
            <label className="label">Amount ($)</label>
            <input
              type="number"
              step="0.01"
              className="input-field"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              style={{ marginBottom: 0 }}
              required
            />
          </div>
          <button type="submit" className="btn" disabled={submitting}>
            {submitting ? "Adding..." : "Add Expense"}
          </button>
        </form>
      </div>

      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Recent Expenses</h2>
        {expenses.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', textAlign: 'center', padding: '2rem 0' }}>No expenses yet! Add the first one above.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {expenses.map(exp => (
              <div key={exp.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: '500' }}>{exp.description}</h3>
                  <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '0.25rem' }}>Paid by {exp.payer?.full_name || exp.payer?.email || `User #${exp.payer_id}`} • {new Date(exp.created_at).toLocaleDateString()}</p>
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                  ${exp.amount.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
