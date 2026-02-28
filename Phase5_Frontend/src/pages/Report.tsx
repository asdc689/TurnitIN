import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import type { SubmissionDetail, RiskLevel } from "../types";
import { useAuth } from "../context/AuthContext";
import UserMenu from "../components/UserMenu";
import {
  Shield, ChevronLeft, Loader2, AlertCircle,
  CheckCircle2, XCircle, FileText, Code2
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

function RiskBadge({ level }: { level: RiskLevel }) {
  const styles = {
    LOW:    "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
    MEDIUM: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800",
    HIGH:   "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${styles[level]}`}>
      {level} RISK
    </span>
  );
}

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  const pct   = Math.round(value * 100);
  const color = pct >= 50 ? "bg-red-500" : pct >= 30 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">{label}</span>
        <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{pct}%</span>
      </div>
      <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Report() {
  const { id }   = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [isLoading, setIsLoading]   = useState(true);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const data = await submissionsApi.getReport(Number(id));
        setSubmission(data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [id]);

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900">

      {/* Navbar */}
      <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800 dark:text-slate-100">Plagiarism Detector</span>
          </Link>
          <UserMenu name={user?.full_name ?? ""} onLogout={logout} />
        </div>
      </nav>

      {/* Main */}
      <main className="max-w-4xl mx-auto px-6 py-8">

        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>

        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-xl p-6 text-center">
            <AlertCircle className="w-6 h-6 mx-auto mb-2" />
            <p className="font-medium">{error}</p>
            <button
              onClick={() => navigate("/dashboard")}
              className="mt-4 text-sm underline"
            >
              Back to Dashboard
            </button>
          </div>

        ) : submission ? (
          <div className="space-y-6">

            {/* Header Card */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-1">
                    Scan Report #{submission.id}
                  </h1>
                  <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    {submission.mode === "text"
                      ? <FileText className="w-4 h-4" />
                      : <Code2 className="w-4 h-4" />
                    }
                    <span className="capitalize">{submission.mode} comparison</span>
                    <span>•</span>
                    <span>{formatDate(submission.created_at)}</span>
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              </div>

              {/* File Names */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">File 1</p>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate" title={submission.file1_name}>
                    {submission.file1_name}
                  </p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">File 2</p>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate" title={submission.file2_name}>
                    {submission.file2_name}
                  </p>
                </div>
              </div>
            </div>

            {/* Failed */}
            {submission.status === "failed" && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-8 text-center shadow-sm">
                <XCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
                <h3 className="font-semibold text-red-800 dark:text-red-400 mb-1 text-lg">Analysis Failed</h3>
                <p className="text-sm text-red-600 dark:text-red-500">
                  {submission.error_message || "An unexpected error occurred during analysis."}
                </p>
              </div>
            )}

            {/* Completed */}
            {submission.status === "completed" && submission.report && (
              <>
                {/* Score Overview */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Similarity Score</h2>
                    <RiskBadge level={submission.report.risk_level} />
                  </div>
                  <div className="text-center py-6">
                    <div className={`text-6xl font-black mb-2 ${
                      submission.report.final_similarity >= 0.5 ? "text-red-600 dark:text-red-400" :
                      submission.report.final_similarity >= 0.3 ? "text-yellow-600 dark:text-yellow-400" :
                      "text-green-600 dark:text-green-400"
                    }`}>
                      {(submission.report.final_similarity * 100).toFixed(1)}%
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium uppercase tracking-wider">
                      Overall Similarity
                    </p>
                  </div>
                </div>

                {/* Algorithm Breakdown */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-6">Algorithm Breakdown</h2>
                  <div className="space-y-5">
                    <ScoreBar label="Cosine Similarity (TF-IDF)"   value={submission.report.scores.cosine} />
                    <ScoreBar label="Jaccard Similarity"           value={submission.report.scores.jaccard} />
                    <ScoreBar label="Longest Common Subsequence"   value={submission.report.scores.lcs} />
                    <ScoreBar label="Winnowing (Code Fingerprint)" value={submission.report.scores.winnowing} />
                    <ScoreBar label="AST Structural Similarity"    value={submission.report.scores.ast} />
                  </div>
                </div>

                {/* Details */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4">Details</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Language</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
                        {submission.report.language || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Processing Time</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.report.processing_time_ms
                          ? `${submission.report.processing_time_ms}ms`
                          : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Algorithm Version</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.report.algorithm_version || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Completed At</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.completed_at ? formatDate(submission.completed_at) : "—"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={() => navigate("/upload")}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm shadow-sm"
                  >
                    New Scan
                  </button>
                </div>
              </>
            )}
          </div>
        ) : null}
      </main>
    </div>
  );
}