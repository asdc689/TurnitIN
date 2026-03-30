import { useState, useEffect, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";
import { Mail, AlertCircle, CheckCircle2, KeyRound, ArrowRight, Home } from "lucide-react";
import axios from "axios";

export default function ForgotPassword() {
  const { setPublicTheme } = useTheme();

  const [email, setEmail]               = useState("");
  const [error, setError]               = useState<string | null>(null);
  const [success, setSuccess]           = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => { setPublicTheme(); }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);
    try {
      const res = await axios.post(
        "http://localhost:8000/api/v1/auth/forgot-password",
        { email }
      );
      setSuccess(res.data.message);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "Something went wrong.");
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 relative overflow-hidden">

      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none -z-10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl" />
      </div>

      {/* Back to Home */}
      <Link
        to="/landing"
        className="absolute top-6 left-6 flex items-center gap-2.5 text-sm font-medium text-slate-400 hover:text-white transition-all duration-200 group"
      >
        <div className="w-9 h-9 bg-slate-800 border border-slate-700 rounded-xl flex items-center justify-center group-hover:bg-indigo-600 group-hover:border-indigo-600 transition-all duration-200">
          <Home className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors duration-200" />
        </div>
        Back to Home
      </Link>

      {/* Card */}
      <div className="w-full max-w-lg bg-slate-900/90 backdrop-blur-sm rounded-3xl border border-slate-800 px-10 py-10">

        {/* Badge */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-full">
            <KeyRound className="w-3.5 h-3.5" />
            Password Recovery
          </div>
        </div>

        {success ? (
          /* ── Success state ── */
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-green-500/10 border border-green-500/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
              <CheckCircle2 className="w-8 h-8 text-green-400" />
            </div>
            <h2 className="text-2xl font-black text-white mb-2">Check your inbox</h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">{success}</p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm font-semibold transition-colors"
            >
              Back to Login
            </Link>
          </div>
        ) : (
          /* ── Form state ── */
          <>
            {/* Heading */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-black text-white mb-2">
                Forgot <span className="text-indigo-400">Password</span>
              </h1>
              <p className="text-slate-400 text-sm">
                Enter your email to receive a password reset link
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-3 mb-6 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                    className="w-full pl-11 pr-4 py-3.5 bg-slate-800/80 border border-slate-700 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:text-indigo-400 text-white font-bold py-3.5 rounded-xl transition-all text-sm shadow-lg shadow-indigo-600/20"
              >
                <Mail className="w-4 h-4" />
                {isSubmitting ? "Sending..." : <>Send Reset Link <ArrowRight className="w-4 h-4" /></>}
              </button>

            </form>

            {/* Back to login */}
            <div className="text-center mt-6">
              <Link
                to="/login"
                className="text-sm text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
              >
                Back to Login
              </Link>
            </div>
          </>
        )}

      </div>
    </div>
  );
}