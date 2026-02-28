import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import UserMenu from "../components/UserMenu";
import {
  Shield, FileText, Code2, Zap, Lock,
  BarChart3, ChevronRight
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
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
      <div className="w-10 h-10 bg-indigo-50 dark:bg-indigo-900/40 rounded-xl flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Landing() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isLoggedIn = !!user;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">

      {/* ── Navbar ── */}
      <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800 dark:text-slate-100">Plagiarism Detector</span>
          </div>

          {isLoggedIn ? (
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate("/dashboard")}
                className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Go to Dashboard
              </button>
              <UserMenu name={user.full_name} onLogout={logout} showDashboardLink={true} />
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-50 dark:bg-indigo-900/40 border border-indigo-100 dark:border-indigo-800 text-indigo-700 dark:text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <Zap className="w-3.5 h-3.5" />
          AI-Powered Plagiarism Detection
        </div>
        <h1 className="text-5xl font-black text-slate-900 dark:text-slate-100 leading-tight mb-6">
          Detect Plagiarism in
          <span className="text-indigo-600 dark:text-indigo-400"> Text & Code</span>
        </h1>
        <p className="text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          The ultimate tool for educators and developers. Instantly compare documents,
          essays, and source code using structural analysis and AI-driven fingerprinting.
        </p>

        {isLoggedIn ? (
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button
              onClick={() => navigate("/upload")}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-sm"
            >
              New Scan
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold px-6 py-3 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
            >
              View History
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/register"
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-sm"
            >
              Start for free
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/login"
              className="flex items-center gap-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold px-6 py-3 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
            >
              Sign in
            </Link>
          </div>
        )}
      </section>

      {/* ── Features ── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-3">Everything you need</h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            A complete plagiarism detection platform for both documents and source code.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard icon={<FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Text & Document Analysis" description="Compare essays, articles, and documents with high accuracy and get a clear similarity score instantly." />
          <FeatureCard icon={<Code2 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Source Code Detection" description="Detect code plagiarism across Python, Java, and C++ by analyzing code structure and logic patterns." />
          <FeatureCard icon={<Zap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Instant Results" description="Get detailed similarity reports in seconds powered by asynchronous background processing." />
          <FeatureCard icon={<BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Detailed Breakdown" description="Get a clear overall similarity score with visual indicators and risk level classification for every scan." />
          <FeatureCard icon={<Lock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Secure & Private" description="Your files are stored securely and only accessible to you. Full authentication with encrypted tokens." />
          <FeatureCard icon={<Shield className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />} title="Submission History" description="Keep track of all your past scans with a full history dashboard and easy access to reports." />
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="bg-indigo-600 dark:bg-indigo-700 rounded-3xl p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to detect plagiarism?
          </h2>
          <p className="text-indigo-200 mb-8 max-w-lg mx-auto">
            {isLoggedIn
              ? "Jump back in and start a new scan from your dashboard."
              : "Create a free account and start analyzing your documents and code today."}
          </p>
          {isLoggedIn ? (
            <button
              onClick={() => navigate("/upload")}
              className="inline-flex items-center gap-2 bg-white hover:bg-slate-100 text-indigo-600 font-semibold px-8 py-3 rounded-xl transition-colors"
            >
              Start a New Scan
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-white hover:bg-slate-100 text-indigo-600 font-semibold px-8 py-3 rounded-xl transition-colors"
            >
              Get started for free
              <ChevronRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-6 py-8 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-indigo-600 rounded-md flex items-center justify-center">
              <Shield className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Plagiarism Detector</span>
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            © {new Date().getFullYear()} Plagiarism Detector. All rights reserved.
          </p>
        </div>
      </footer>

    </div>
  );
}