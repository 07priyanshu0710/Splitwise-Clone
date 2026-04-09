"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, removeToken } from "@/lib/api";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { NeoCard } from "@/components/ui/NeoCard";
import { NeoButton } from "@/components/ui/NeoButton";
import { NeoInput } from "@/components/ui/NeoInput";
import { LogOut, Plus, Users, ArrowRight, DollarSign } from "lucide-react";

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
      const groupData = await api.getGroups();
      setGroups(groupData);
    } catch (err) {
      alert(err.message || "Failed to create group");
    } finally {
      setCreatingGroup(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <NeoCard className="p-10 flex flex-col items-center max-w-md w-full bg-neo-secondary rotate-1 shadow-neo-xl">
          <div className="w-16 h-16 border-4 border-black border-t-white rounded-full animate-spin-slow mb-6" />
          <h2 className="text-2xl font-black uppercase tracking-widest text-center">Loading Dashboard</h2>
          <p className="font-bold text-center mt-2">Server might be waking up (up to 30s).</p>
        </NeoCard>
      </div>
    );
  }

  const totalOwed = balances.filter(b => b.user_id === user?.id).reduce((acc, curr) => acc + curr.amount, 0);
  const totalOwedToMe = balances.filter(b => b.owes_to_id === user?.id).reduce((acc, curr) => acc + curr.amount, 0);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 lg:p-12 pb-24">
      
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-6 relative z-10">
        <div>
          <div className="inline-block bg-neo-accent border-4 border-black px-4 py-1 -rotate-2 mb-4 shadow-neo-sm">
            <span className="font-black uppercase tracking-widest text-sm text-black">Dashboard</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tight text-stroke relative z-10">
            Welcome, {user?.full_name?.split(' ')[0] || 'User'}
          </h1>
          <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tight text-neo-secondary absolute top-12 md:top-10 left-0 -z-10">
            Welcome, {user?.full_name?.split(' ')[0] || 'User'}
          </h1>
        </div>
        <NeoButton onClick={handleLogout} variant="outline" className="h-12 px-6 shadow-neo-sm">
          <LogOut className="w-4 h-4 mr-2" strokeWidth={3} />
          LOGOUT
        </NeoButton>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 md:gap-12 relative z-20">
        
        {/* Left Column - Balances */}
        <div className="lg:col-span-5 flex flex-col gap-8 md:gap-12">
          
          {/* Overall Balances */}
          <NeoCard className="p-6 md:p-8 bg-white rotate-1">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b-4 border-black">
              <DollarSign className="w-8 h-8 stroke-[3px]" />
              <h2 className="text-2xl font-black uppercase">Balances</h2>
            </div>
            
            <div className="space-y-6">
              <div className="flex justify-between items-center bg-red-100 border-4 border-black p-4 -rotate-1 shadow-neo-sm">
                <span className="font-bold uppercase text-sm tracking-widest">You Owe</span>
                <span className="font-black text-2xl text-red-600">${totalOwed.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center bg-green-100 border-4 border-black p-4 rotate-1 shadow-neo-sm">
                <span className="font-bold uppercase text-sm tracking-widest">Owed to You</span>
                <span className="font-black text-2xl text-green-600">${totalOwedToMe.toFixed(2)}</span>
              </div>
            </div>
          </NeoCard>

          {/* Settle Up Needs */}
          <NeoCard className="p-6 md:p-8 bg-neo-muted -rotate-1">
            <h2 className="text-2xl font-black uppercase mb-6 pb-4 border-b-4 border-black">Settle Up Needs</h2>
            
            {balances.length === 0 ? (
              <div className="bg-white border-4 border-black p-6 rotate-2 shadow-neo-sm text-center">
                <p className="font-bold uppercase tracking-widest">All Settled Up!</p>
              </div>
            ) : (
              <ul className="space-y-4">
                {balances.map(b => {
                  const amIOwed = b.owes_to_id === user?.id;
                  const otherParam = amIOwed ? b.user : b.owes_to;
                  const otherName = otherParam?.full_name || otherParam?.email || `User #${amIOwed ? b.user_id : b.owes_to_id}`;

                  return (
                    <li key={b.id} className="bg-white border-4 border-black p-4 flex justify-between items-center shadow-[4px_4px_0px_0px_#000] hover:-translate-y-1 hover:translate-x-1 transition-transform">
                      <span className="font-bold">{otherName}</span>
                      <div className={cn(
                        "font-black uppercase px-2 py-1 border-2 border-black",
                        amIOwed ? "bg-green-300 text-green-900" : "bg-red-300 text-red-900"
                      )}>
                        {amIOwed ? `OWES $${b.amount.toFixed(2)}` : `YOU OWE $${b.amount.toFixed(2)}`}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </NeoCard>
        </div>

        {/* Right Column - Groups */}
        <div className="lg:col-span-7">
          <NeoCard className="p-6 md:p-8 bg-neo-secondary h-full flex flex-col rotate-1">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b-4 border-black">
              <Users className="w-8 h-8 stroke-[3px]" />
              <h2 className="text-2xl font-black uppercase">Your Groups</h2>
            </div>

            <div className="flex-1 mb-10">
              {groups.length === 0 ? (
                <div className="bg-white border-4 border-black p-8 -rotate-1 shadow-neo-sm text-center">
                  <p className="font-bold uppercase tracking-widest text-lg">No groups yet.</p>
                  <p className="mt-2 font-bold opacity-60">Create one below to start splitting!</p>
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-6">
                  {groups.map(group => (
                    <Link href={`/groups/${group.id}`} key={group.id} className="block group">
                      <div className="bg-white border-4 border-black p-6 shadow-neo-sm transition-all duration-200 group-hover:-translate-y-2 group-hover:shadow-neo group-hover:-rotate-2 h-full flex flex-col justify-between">
                        <h3 className="font-black text-xl uppercase mb-4 line-clamp-2">{group.name}</h3>
                        <div className="flex justify-between items-center pt-4 border-t-2 border-black/20">
                          <span className="font-bold uppercase text-xs tracking-widest text-black/60">View Details</span>
                          <ArrowRight className="w-5 h-5 stroke-[4px] group-hover:translate-x-1 transition-transform" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <form onSubmit={handleCreateGroup} className="bg-white border-4 border-black p-6 mt-auto shadow-neo-sm -rotate-1">
              <h3 className="font-black uppercase text-xl mb-4 flex items-center gap-2">
                <Plus strokeWidth={4} />
                Create New Group
              </h3>
              <div className="flex flex-col sm:flex-row gap-4">
                <NeoInput
                  className="flex-1"
                  placeholder="TRIP TO PARIS..."
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  required
                />
                <NeoButton type="submit" variant="primary" disabled={creatingGroup} className="w-full sm:w-auto h-14">
                  {creatingGroup ? "WAIT..." : "CREATE"}
                </NeoButton>
              </div>
            </form>
          </NeoCard>
        </div>

      </div>
    </div>
  );
}
