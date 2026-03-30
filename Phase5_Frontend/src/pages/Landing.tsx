import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import UserMenu from "../components/UserMenu";
import {
  Shield, FileText, Code2, Zap, Lock,
  BarChart3, ChevronRight, Sparkles
} from "lucide-react";

// ── Feature Card ──────────────────────────────────────────────────────────────

function FeatureCard({
  icon, title, description
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 hover:border-indigo-500/50 hover:bg-slate-800 transition-all duration-200">
      <div className="w-10 h-10 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
      <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Landing() {
  const { user, logout } = useAuth();
  const { setPublicTheme } = useTheme();
  const navigate = useNavigate();
  const isLoggedIn = !!user;

  // Force dark mode for this page — independent of user's app preference
  useEffect(() => {
    setPublicTheme();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">

      {/* ── Navbar ── */}
      <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-40 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-100">Origify</span>
          </div>

          {isLoggedIn ? (
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate("/dashboard")}
                className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Go to Dashboard
              </button>
              <UserMenu name={user.full_name} onLogout={logout} showDashboardLink={true} />
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="text-sm font-medium text-slate-400 hover:text-slate-100 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative max-w-6xl mx-auto px-6 py-28 text-center overflow-hidden">

        {/* Glow background */}
        <div className="absolute inset-0 -z-10 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-indigo-600/10 rounded-full blur-3xl" />
        </div>

        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          AI-Powered Plagiarism Detection
        </div>

        <h1 className="text-5xl sm:text-6xl font-black text-white leading-tight mb-6">
          Detect Plagiarism in
          <br />
          <span className="text-indigo-400">Text & Code</span>
        </h1>

        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          The ultimate tool for educators and developers. Instantly compare documents,
          essays, and source code using structural analysis and AI-driven fingerprinting.
        </p>

        {isLoggedIn ? (
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button
              onClick={() => navigate("/upload")}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-lg shadow-indigo-600/20"
            >
              New Scan
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-6 py-3 rounded-xl border border-slate-700 transition-colors"
            >
              View History
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/register"
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-lg shadow-indigo-600/20"
            >
              Start for free
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/login"
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-6 py-3 rounded-xl border border-slate-700 transition-colors"
            >
              Sign in
            </Link>
          </div>
        )}
      </section>

      {/* ── Features ── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-3">Everything you need</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            A complete plagiarism detection platform for both documents and source code.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard icon={<FileText className="w-5 h-5 text-indigo-400" />} title="Text & Document Analysis" description="Compare essays, articles, and documents with high accuracy and get a clear similarity score instantly." />
          <FeatureCard icon={<Code2 className="w-5 h-5 text-indigo-400" />} title="Source Code Detection" description="Detect code plagiarism across Python, Java, and C++ by analyzing code structure and logic patterns." />
          <FeatureCard icon={<Zap className="w-5 h-5 text-indigo-400" />} title="Instant Results" description="Get detailed similarity reports in seconds powered by asynchronous background processing." />
          <FeatureCard icon={<BarChart3 className="w-5 h-5 text-indigo-400" />} title="Detailed Breakdown" description="Get a clear overall similarity score with visual indicators and risk level classification for every scan." />
          <FeatureCard icon={<Lock className="w-5 h-5 text-indigo-400" />} title="Secure & Private" description="Your files are stored securely and only accessible to you. Full authentication with encrypted tokens." />
          <FeatureCard icon={<Shield className="w-5 h-5 text-indigo-400" />} title="Submission History" description="Keep track of all your past scans with a full history dashboard and easy access to reports." />
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="relative bg-indigo-600/10 border border-indigo-500/20 rounded-3xl p-12 text-center overflow-hidden">
          <div className="absolute inset-0 -z-10 pointer-events-none">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[200px] bg-indigo-600/20 rounded-full blur-3xl" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to detect plagiarism?
          </h2>
          <p className="text-slate-400 mb-8 max-w-lg mx-auto">
            {isLoggedIn
              ? "Jump back in and start a new scan from your dashboard."
              : "Create a free account and start analyzing your documents and code today."}
          </p>
          {isLoggedIn ? (
            <button
              onClick={() => navigate("/upload")}
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-xl transition-colors shadow-lg shadow-indigo-600/20"
            >
              Start a New Scan
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-xl transition-colors shadow-lg shadow-indigo-600/20"
            >
              Get started for free
              <ChevronRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800 bg-slate-950 px-6 py-8 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-indigo-600 rounded-md flex items-center justify-center">
              <Shield className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-400">Origify</span>
          </div>
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} Origify. All rights reserved.
          </p>
        </div>
      </footer>

    </div>
  );
}