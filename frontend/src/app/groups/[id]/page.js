"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";
import { NeoCard } from "@/components/ui/NeoCard";
import { NeoButton } from "@/components/ui/NeoButton";
import { NeoInput } from "@/components/ui/NeoInput";
import { ArrowLeft, UserPlus, Receipt, Users } from "lucide-react";

export default function GroupDetail() {
  const { id } = useParams();
  const router = useRouter();

  const [group, setGroup] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [loading, setLoading] = useState(true);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [memberIdentifier, setMemberIdentifier] = useState("");
  const [addingMember, setAddingMember] = useState(false);
  const [settlementAmounts, setSettlementAmounts] = useState({});
  const [settlingBalanceId, setSettlingBalanceId] = useState(null);

  useEffect(() => {
    const fetchGroupData = async () => {
      try {
        const [grpData, expData, userData, balanceData, settlementData] = await Promise.all([
          api.getGroup(id),
          api.getGroupExpenses(id),
          api.getMe(),
          api.getGroupBalances(id),
          api.getGroupSettlements(id),
        ]);
        setGroup(grpData);
        setExpenses(expData);
        setCurrentUser(userData);
        setBalances(balanceData);
        setSettlements(settlementData);
      } catch (err) {
        console.error(err);
        if (err.message === "Unauthorized") router.push("/");
      } finally {
        setLoading(false);
      }
    };

    fetchGroupData();
  }, [id, router]);

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
      const [expData, balanceData] = await Promise.all([
        api.getGroupExpenses(id),
        api.getGroupBalances(id),
      ]);
      setExpenses(expData);
      setBalances(balanceData);
    } catch (err) {
      alert(err.message || "Failed to create expense");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSettlement = async (e, balance) => {
    e.preventDefault();
    const settlementAmount = Number(settlementAmounts[balance.id]);
    if (!Number.isFinite(settlementAmount) || settlementAmount <= 0) {
      alert("Enter a valid settlement amount");
      return;
    }
    if (settlementAmount > balance.amount) {
      alert(`You can settle at most INR ${balance.amount.toFixed(2)}`);
      return;
    }

    setSettlingBalanceId(balance.id);
    try {
      await api.createSettlement({
        payee_id: balance.owes_to_id,
        amount: settlementAmount,
        group_id: Number(id),
        description: "Group settlement",
      });
      const [balanceData, settlementData] = await Promise.all([
        api.getGroupBalances(id),
        api.getGroupSettlements(id),
      ]);
      setBalances(balanceData);
      setSettlements(settlementData);
      setSettlementAmounts((values) => ({ ...values, [balance.id]: "" }));
    } catch (err) {
      alert(err.message || "Failed to record settlement");
    } finally {
      setSettlingBalanceId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <NeoCard className="p-10 flex flex-col items-center max-w-md w-full bg-neo-accent -rotate-1 shadow-neo-xl">
          <div className="w-16 h-16 border-4 border-black border-t-white rounded-full animate-spin-slow mb-6" />
          <h2 className="text-2xl font-black uppercase tracking-widest text-center">Loading Group...</h2>
        </NeoCard>
      </div>
    );
  }

  if (!group) return (
    <div className="min-h-screen flex items-center justify-center">
      <NeoCard className="p-8 bg-red-400 rotate-2"><h2 className="text-2xl font-black">GROUP NOT FOUND</h2></NeoCard>
    </div>
  );

  const canManageMembers = group.members.some(
    (member) => member.user_id === currentUser?.id && member.role === "admin"
  );
  const myDebts = balances.filter((balance) => balance.user_id === currentUser?.id);

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 lg:p-12 pb-24">

      {/* Header */}
      <div className="mb-12">
        <Link href="/dashboard" className="inline-flex items-center font-bold uppercase tracking-widest mb-6 hover:text-neo-accent hover:-translate-x-2 transition-all group border-b-4 border-transparent hover:border-black">
          <ArrowLeft className="w-5 h-5 mr-2 stroke-[3px]" /> Back to Dashboard
        </Link>
        <div className="relative inline-block w-full">
          <NeoCard className="bg-neo-accent p-6 md:p-10 rotate-1 relative z-10 w-full mb-8">
            <h1 className="text-4xl md:text-6xl font-black uppercase tracking-tight line-clamp-2">
              {group.name}
            </h1>
            <p className="font-bold text-black border-2 border-black bg-white inline-block px-3 py-1 mt-4 rotate-2 shadow-[4px_4px_0px_0px_#000]">
              ID: {group.id}
            </p>
          </NeoCard>
          <div className="absolute top-2 left-2 w-full h-full bg-black z-0 border-4 border-black" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12">
        
        {/* Left Column - Forms */}
        <div className="flex flex-col gap-8 md:gap-12">
          
          {/* Add Expense Form */}
          <NeoCard className="p-6 md:p-8 bg-neo-secondary -rotate-1">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b-4 border-black">
              <Receipt className="w-8 h-8 stroke-[3px]" />
              <h2 className="text-2xl font-black uppercase">Add an Expense</h2>
            </div>
            
            <form onSubmit={handleAddExpense} className="space-y-6">
              <NeoInput
                label="Description"
                placeholder="DINNER, TAXI, GROCERIES..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
              <NeoInput
                label="Amount (₹)"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
              <NeoButton type="submit" variant="primary" disabled={submitting} className="w-full">
                {submitting ? "ADDING..." : "ADD EXPENSE"}
              </NeoButton>
            </form>
          </NeoCard>

          {/* Members section */}
          <NeoCard className="p-6 md:p-8 bg-neo-muted rotate-1">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b-4 border-black">
              <Users className="w-8 h-8 stroke-[3px]" />
              <h2 className="text-2xl font-black uppercase">Group Members</h2>
            </div>

            <div className="flex flex-wrap gap-3 mb-8">
              {group.members.map((m) => (
                <div key={m.id} className="bg-white border-4 border-black px-3 py-2 shadow-neo-sm font-bold flex items-center gap-2 hover:-translate-y-1 transition-transform">
                   <div className="w-6 h-6 bg-neo-secondary border-2 border-black rounded-full flex items-center justify-center -ml-1">👤</div>
                   {m.user.full_name || m.user.email} <span className="opacity-50 text-xs tracking-widest uppercase">({m.role})</span>
                </div>
              ))}
            </div>

            {canManageMembers ? (
              <form onSubmit={handleAddMember} className="border-t-4 border-black pt-6">
                <h3 className="font-black uppercase mb-4 flex items-center gap-2">
                  <UserPlus className="w-5 h-5 stroke-[3px]" /> Add Member
                </h3>
                <div className="space-y-4">
                  <NeoInput
                    placeholder="FRIEND@EXAMPLE.COM OR +91 98765..."
                    value={memberIdentifier}
                    onChange={(e) => setMemberIdentifier(e.target.value)}
                    required
                  />
                  <NeoButton type="submit" variant="secondary" disabled={addingMember} className="w-full">
                    {addingMember ? "ADDING..." : "ADD MEMBER"}
                  </NeoButton>
                </div>
              </form>
            ) : (
              <p className="border-t-4 border-black pt-6 font-bold uppercase text-sm tracking-widest">
                Only group admins can add members.
              </p>
            )}
          </NeoCard>

          {/* Settle up */}
          <NeoCard className="p-6 md:p-8 bg-neo-secondary -rotate-1">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b-4 border-black">
              <span className="text-3xl font-black">₹</span>
              <h2 className="text-2xl font-black uppercase">Settle Up</h2>
            </div>

            {myDebts.length === 0 ? (
              <p className="bg-white border-4 border-black p-4 font-bold uppercase shadow-neo-sm">
                You have no outstanding debt in this group.
              </p>
            ) : (
              <div className="space-y-6">
                {myDebts.map((balance) => (
                  <form
                    key={balance.id}
                    onSubmit={(e) => handleSettlement(e, balance)}
                    className="bg-white border-4 border-black p-4 shadow-neo-sm space-y-4"
                  >
                    <p className="font-black uppercase">
                      You owe {balance.owes_to?.full_name || balance.owes_to?.email || `User #${balance.owes_to_id}`}
                    </p>
                    <p className="font-black text-xl text-red-600">INR {balance.amount.toFixed(2)}</p>
                    <NeoInput
                      label="Amount to pay (₹)"
                      type="number"
                      min="0.01"
                      max={balance.amount}
                      step="0.01"
                      placeholder={balance.amount.toFixed(2)}
                      value={settlementAmounts[balance.id] || ""}
                      onChange={(e) => setSettlementAmounts((values) => ({
                        ...values,
                        [balance.id]: e.target.value,
                      }))}
                      required
                    />
                    <NeoButton
                      type="submit"
                      variant="primary"
                      disabled={settlingBalanceId === balance.id}
                      className="w-full"
                    >
                      {settlingBalanceId === balance.id ? "SETTLING..." : "RECORD PAYMENT"}
                    </NeoButton>
                  </form>
                ))}
              </div>
            )}
          </NeoCard>
        </div>

        {/* Right Column - Financial history */}
        <div className="flex flex-col gap-8 md:gap-12">
          <NeoCard className="p-6 md:p-8 bg-white rotate-1">
            <h2 className="text-2xl font-black uppercase mb-6 pb-4 border-b-4 border-black flex justify-between items-center">
              Recent Expenses
              <span className="bg-neo-accent border-4 border-black px-3 py-1 rotate-3 shadow-[4px_4px_0px_0px_#000]">
                 {expenses.length} 
              </span>
            </h2>

            {expenses.length === 0 ? (
              <div className="bg-neo-canvas border-4 border-black p-8 text-center -rotate-2 mt-8 shadow-neo-sm">
                 <p className="font-bold uppercase tracking-widest text-lg">No expenses yet.</p>
                 <p className="opacity-60 max-w-[200px] mx-auto mt-2">Time to spend some money!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {expenses.map(exp => (
                  <div key={exp.id} className="bg-neo-canvas border-4 border-black p-4 flex justify-between items-center shadow-[4px_4px_0px_0px_#000] hover:-translate-y-1 hover:translate-x-1 transition-transform">
                    <div>
                      <h3 className="font-black text-xl uppercase mb-1">{exp.description}</h3>
                      <p className="font-bold text-xs uppercase tracking-widest text-black/60">
                        PAID BY {exp.payer?.full_name || exp.payer?.email || `USER #${exp.payer_id}`}
                      </p>
                      <p className="font-bold text-xs uppercase mt-1">
                        {new Date(exp.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="bg-neo-secondary border-4 border-black font-black text-xl px-4 py-2 rotate-2 shadow-[4px_4px_0px_0px_#000]">
                      INR {exp.amount.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </NeoCard>

          <NeoCard className="p-6 md:p-8 bg-neo-muted -rotate-1">
            <h2 className="text-2xl font-black uppercase mb-6 pb-4 border-b-4 border-black flex justify-between items-center">
              Settlement History
              <span className="bg-white border-4 border-black px-3 py-1 rotate-3 shadow-[4px_4px_0px_0px_#000]">
                {settlements.length}
              </span>
            </h2>

            {settlements.length === 0 ? (
              <p className="bg-white border-4 border-black p-6 text-center font-bold uppercase shadow-neo-sm">
                No payments recorded yet.
              </p>
            ) : (
              <div className="space-y-4">
                {settlements.map((settlement) => (
                  <div key={settlement.id} className="bg-white border-4 border-black p-4 shadow-neo-sm">
                    <p className="font-black uppercase">
                      {settlement.payer?.full_name || settlement.payer?.email} paid {settlement.payee?.full_name || settlement.payee?.email}
                    </p>
                    <div className="flex justify-between gap-4 mt-2 font-bold text-sm uppercase">
                      <span>{new Date(settlement.created_at).toLocaleDateString()}</span>
                      <span>INR {settlement.amount.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </NeoCard>
        </div>

      </div>
    </div>
  );
}
