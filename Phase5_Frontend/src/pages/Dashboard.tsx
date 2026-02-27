import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { SubmissionListItem, RiskLevel } from "../types";
import {
  Shield, LogOut, Upload, Clock, CheckCircle2,
  XCircle, Loader2, ChevronRight, FileText, Code2, Trash2
} from "lucide-react";

// Helpers
// Generates a color-coded badge based on the risk level
function RiskBadge({ level }: { level: RiskLevel }) {
  const styles = {
    LOW:    "bg-green-100 text-green-700",
    MEDIUM: "bg-yellow-100 text-yellow-700",
    HIGH:   "bg-red-100 text-red-700",
  };
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${styles[level]}`}>
      {level}
    </span>
  );
}

// Returns the appropriate Lucide icon based on the Celery task status
function StatusIcon({ status }: { status: string }) {
  if (status === "completed")  return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === "failed")     return <XCircle className="w-4 h-4 text-red-500" />;
  if (status === "processing") return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
  return <Clock className="w-4 h-4 text-slate-400" />;
}

// Formats the ISO timestamp into a clean, human-readable date
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

// Component
export default function Dashboard() {
  // State & Hooks
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([]);
  const [isLoading, setIsLoading]     = useState(true);
  const [error, setError]             = useState<string | null>(null);
  
  // Tracks which specific row is currently being deleted to show a targeted spinner
  const [deletingId, setDeletingId]   = useState<number | null>(null);

  // Fetch data on initial mount
  useEffect(() => {
    fetchHistory();
  }, []);

  // Handlers
  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      setError(null);
      // Calls the backend to get the paginated list of previous scans
      const data = await submissionsApi.getHistory();
      setSubmissions(data.submissions);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    // Safety check to prevent accidental deletions
    if (!confirm("Are you sure you want to delete this submission?")) return;
    
    setDeletingId(id);
    try {
      await submissionsApi.delete(id);
      // Optimistic UI update: remove the item from the screen immediately
      // instead of forcing a full page reload or a second API fetch
      setSubmissions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      alert(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  // Render
  return (
    <div className="min-h-screen bg-slate-100">

      {/* Navbar */}
      <nav className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800">Plagiarism Detector</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
            <p className="text-slate-500 mt-1">View and manage your submissions</p>
          </div>
          <button
            onClick={() => navigate("/upload")}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm"
          >
            <Upload className="w-4 h-4" />
            New Submission
          </button>
        </div>

        {/* Content Routing */}
        {isLoading ? (
          // Loading State
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : error ? (
          // Error State
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6 text-center">
            <p className="font-medium">{error}</p>
            <button onClick={fetchHistory} className="mt-3 text-sm underline">
              Try again
            </button>
          </div>
        ) : submissions.length === 0 ? (
          // Empty State
          <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center">
            <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-7 h-7 text-slate-400" />
            </div>
            <h3 className="font-semibold text-slate-700 mb-2">No submissions yet</h3>
            <p className="text-slate-500 text-sm mb-6">
              Upload two files to start detecting plagiarism
            </p>
            <button
              onClick={() => navigate("/upload")}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
            >
              Make your first submission
            </button>
          </div>
        ) : (
          // Data Table
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Files</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Mode</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Status</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Similarity</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Risk</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">Date</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                    
                    {/* File Names */}
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-800 truncate max-w-[200px]">
                        {s.file1_name}
                      </div>
                      <div className="text-xs text-slate-400 truncate max-w-[200px]">
                        {s.file2_name}
                      </div>
                    </td>
                    
                    {/* Mode (Text vs Code) */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-sm text-slate-600">
                        {s.mode === "text"
                          ? <FileText className="w-3.5 h-3.5" />
                          : <Code2 className="w-3.5 h-3.5" />
                        }
                        <span className="capitalize">{s.mode}</span>
                      </div>
                    </td>
                    
                    {/* Status with Animated Icons */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5">
                        <StatusIcon status={s.status} />
                        <span className="text-sm text-slate-600 capitalize">{s.status}</span>
                      </div>
                    </td>
                    
                    {/* Similarity Score */}
                    <td className="px-6 py-4">
                      {s.final_similarity !== null
                        ? <span className="text-sm font-semibold text-slate-800">
                            {(s.final_similarity * 100).toFixed(1)}%
                          </span>
                        : <span className="text-sm text-slate-400">—</span>
                      }
                    </td>
                    
                    {/* Risk Level Badge */}
                    <td className="px-6 py-4">
                      {s.risk_level
                        ? <RiskBadge level={s.risk_level} />
                        : <span className="text-sm text-slate-400">—</span>
                      }
                    </td>
                    
                    {/* Date */}
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {formatDate(s.created_at)}
                    </td>
                    
                    {/* Actions (Report Link & Delete Button) */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4 justify-end">
                        {s.status === "completed" && (
                          <Link
                            to={`/report/${s.id}`}
                            className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                          >
                            Report <ChevronRight className="w-3.5 h-3.5" />
                          </Link>
                        )}
                        <button
                          onClick={() => handleDelete(s.id)}
                          disabled={deletingId === s.id}
                          className="text-slate-400 hover:text-red-500 transition-colors"
                          title="Delete submission"
                        >
                          {deletingId === s.id
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <Trash2 className="w-4 h-4" />
                          }
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}