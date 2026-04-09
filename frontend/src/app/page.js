"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, getToken } from "@/lib/api";
import { NeoButton } from "@/components/ui/NeoButton";
import { NeoInput } from "@/components/ui/NeoInput";
import { NeoCard } from "@/components/ui/NeoCard";
import { ArrowRight, Star } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Redirect if already logged in
    if (getToken()) {
      router.push("/dashboard");
    }
    // Warm up the backend while user fills in the form
    fetch('https://splitwise-clone-96iy.onrender.com/health').catch(() => {});
  }, [router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        const data = await api.login(email, password);
        setToken(data.access_token);
        router.push("/dashboard");
      } else {
        await api.register(email, password, fullName, mobileNumber || null);
        // Automatically log them in after registration
        const data = await api.login(email, password);
        setToken(data.access_token);
        router.push("/dashboard");
      }
    } catch (err) {
        // Safe check for err.response or raw error string
        if (err.response && err.response.data && err.response.data.detail) {
            setError(err.response.data.detail);
        } else {
            setError(err.message || "An error occurred");
        }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden">
      {/* Decorative background elements */}
      <Star className="absolute top-10 left-10 w-16 h-16 fill-neo-secondary stroke-[3px] -rotate-12 animate-spin-slow opacity-50" />
      <div className="absolute top-20 right-20 w-32 h-32 bg-neo-muted border-4 border-black rotate-12 opacity-50" />
      <div className="absolute bottom-20 left-1/4 w-24 h-24 rounded-full bg-neo-accent border-4 border-black -rotate-6 opacity-30" />
      
      <div className="w-full max-w-lg relative z-10">
        <div className="text-center mb-10 -rotate-2">
          <div className="inline-block relative">
            <h1 className="text-6xl md:text-7xl font-black uppercase tracking-tighter text-black text-stroke relative z-10">
              Splitwise
            </h1>
            <h1 className="text-6xl md:text-7xl font-black uppercase tracking-tighter text-neo-accent absolute top-1 left-1">
              Splitwise
            </h1>
            <div className="absolute -bottom-4 -right-6 bg-neo-secondary border-4 border-black px-4 py-1 rotate-6 shadow-neo-sm z-20">
              <span className="font-bold uppercase tracking-widest text-sm">Clone</span>
            </div>
          </div>
        </div>

        <NeoCard className="p-8 md:p-10 rotate-1">
          <div className="mb-8">
            <h2 className="text-3xl font-black uppercase">
              {isLogin ? "Welcome Back!" : "Join the Party."}
            </h2>
            <p className="font-bold text-black/60 mt-2">
              {isLogin ? "Login to track your expenses." : "Create an account to get started."}
            </p>
          </div>

          {error && (
            <div className="bg-neo-accent border-4 border-black p-4 mb-6 shadow-neo-sm font-bold">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <NeoInput
                label="Full Name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="JOHN DOE"
              />
            )}

            <NeoInput
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="YOU@EXAMPLE.COM"
            />

            {!isLogin && (
              <NeoInput
                label="Mobile Number (Optional)"
                type="tel"
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value)}
                placeholder="+91 9876543210"
              />
            )}

            <NeoInput
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />

            <NeoButton 
              type="submit" 
              className="w-full mt-8 text-lg"
              disabled={loading}
              variant={isLogin ? "primary" : "secondary"}
            >
              <span className="mr-2">
                {loading ? "PROCESSING..." : (isLogin ? "SIGN IN" : "CREATE ACCOUNT")}
              </span>
              {!loading && <ArrowRight className="w-5 h-5 stroke-[4px]" />}
            </NeoButton>
          </form>

          <div className="mt-8 pt-6 border-t-4 border-black text-center">
            <span className="font-bold uppercase text-sm">
              {isLogin ? "NEW HERE? " : "ALREADY IN? "}
            </span>
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="font-black uppercase text-sm underline decoration-4 underline-offset-4 hover:text-neo-accent transition-colors"
              type="button"
            >
              {isLogin ? "SIGN UP" : "SIGN IN"}
            </button>
          </div>
        </NeoCard>
      </div>
    </div>
  );
}
