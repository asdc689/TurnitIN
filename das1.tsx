import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { SubmissionListItem, RiskLevel } from "../types";
import {
  Shield, LogOut, Upload, Clock, CheckCircle2,
  XCircle, Loader2, ChevronRight, ChevronLeft,
  FileText, Code2, Trash2, User, RefreshCw
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

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

function StatusIcon({ status }: { status: string }) {
  if (status === "completed")                          return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === "failed")                             return <XCircle className="w-4 h-4 text-red-500" />;
  if (status === "processing" || status === "pending") return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
  return <Clock className="w-4 h-4 text-slate-400" />;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PAGE_SIZE = 8;

// ── Component ─────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([]);
  const [isLoading, setIsLoading]       = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [deletingId, setDeletingId]     = useState<number | null>(null);

  // ── Pagination ──
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages]   = useState(1);
  const [total, setTotal]             = useState(0);

  // ── Filters ──
  const [modeFilter, setModeFilter] = useState<"" | "text" | "code">("");
  const [riskFilter, setRiskFilter] = useState<"" | "LOW" | "MEDIUM" | "HIGH">("");
  const [sortOrder, setSortOrder]   = useState<"desc" | "asc">("desc");

  // ── Data Fetching ─────────────────────────────────────────────────────────

  const fetchHistory = useCallback(async (page = 1, showRefresh = false) => {
    try {
      showRefresh ? setIsRefreshing(true) : setIsLoading(true);
      setError(null);

      const data = await submissionsApi.getHistory(
        page, PAGE_SIZE,
        modeFilter || undefined,
        riskFilter || undefined,
        sortOrder
      );

      setSubmissions(data.submissions);
      setTotal(data.total);
      setTotalPages(Math.ceil(data.total / PAGE_SIZE) || 1);
      setCurrentPage(page);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [modeFilter, riskFilter, sortOrder]);

  // Re-fetch from page 1 whenever filters change
  useEffect(() => {
    fetchHistory(1);
  }, [modeFilter, riskFilter, sortOrder, fetchHistory]);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this submission?")) return;
    setDeletingId(id);
    try {
      await submissionsApi.delete(id);
      const newTotal    = total - 1;
      const maxPage     = Math.ceil(newTotal / PAGE_SIZE) || 1;
      const pageToFetch = currentPage > maxPage ? maxPage : currentPage;
      await fetchHistory(pageToFetch);
    } catch (err) {
      alert(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handlePageChange = (page: number) => {
    if (page < 1 || page > totalPages || page === currentPage) return;
    fetchHistory(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearFilters = () => {
    setModeFilter("");
    setRiskFilter("");
    setSortOrder("desc");
  };

  const hasActiveFilters = modeFilter || riskFilter || sortOrder !== "desc";

  // ── Render ────────────────────────────────────────────────────────────────

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
            <Link
              to="/profile"
              className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-indigo-600 transition-colors"
            >
              <User className="w-4 h-4" />
              {user?.full_name}
            </Link>
            <span className="text-slate-300">|</span>
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
            <p className="text-slate-500 mt-1">
              {total > 0
                ? `${total} submission${total !== 1 ? "s" : ""}${hasActiveFilters ? " matching filters" : " total"}`
                : "View and manage your submissions"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchHistory(currentPage, true)}
              disabled={isRefreshing}
              title="Refresh"
              className="p-2.5 text-slate-500 hover:text-indigo-600 border border-slate-200 bg-white rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={() => navigate("/upload")}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm shadow-sm"
            >
              <Upload className="w-4 h-4" />
              New Submission
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center flex-wrap gap-3 mb-6">
          <select
            value={modeFilter}
            onChange={(e) => setModeFilter(e.target.value as typeof modeFilter)}
            className="text-sm border border-slate-200 bg-white rounded-lg px-3 py-2 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Modes</option>
            <option value="text">Text</option>
            <option value="code">Code</option>
          </select>

          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as typeof riskFilter)}
            className="text-sm border border-slate-200 bg-white rounded-lg px-3 py-2 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Risk Levels</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
          </select>

          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as "desc" | "asc")}
            className="text-sm border border-slate-200 bg-white rounded-lg px-3 py-2 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-slate-400 hover:text-red-500 transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6 text-center">
            <p className="font-medium">{error}</p>
            <button onClick={() => fetchHistory(1)} className="mt-3 text-sm underline">
              Try again
            </button>
          </div>
        ) : submissions.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center shadow-sm">
            <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-7 h-7 text-slate-400" />
            </div>
            <h3 className="font-semibold text-slate-700 mb-2">
              {hasActiveFilters ? "No submissions match your filters" : "No submissions yet"}
            </h3>
            <p className="text-slate-500 text-sm mb-6">
              {hasActiveFilters
                ? "Try clearing your filters to see all submissions"
                : "Upload two files to start detecting plagiarism"}
            </p>
            {hasActiveFilters ? (
              <button
                onClick={clearFilters}
                className="bg-slate-600 hover:bg-slate-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
              >
                Clear filters
              </button>
            ) : (
              <button
                onClick={() => navigate("/upload")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm shadow-sm"
              >
                Make your first submission
              </button>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">

            <div className="overflow-x-auto">
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

                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-slate-800 truncate max-w-[200px]" title={s.file1_name}>
                          {s.file1_name}
                        </div>
                        <div className="text-xs text-slate-400 truncate max-w-[200px]" title={s.file2_name}>
                          {s.file2_name}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-sm text-slate-600">
                          {s.mode === "text"
                            ? <FileText className="w-3.5 h-3.5" />
                            : <Code2 className="w-3.5 h-3.5" />
                          }
                          <span className="capitalize">{s.mode}</span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5">
                          <StatusIcon status={s.status} />
                          <span className="text-sm text-slate-600 capitalize">{s.status}</span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        {s.final_similarity !== null
                          ? <span className="text-sm font-semibold text-slate-800">
                              {(s.final_similarity * 100).toFixed(1)}%
                            </span>
                          : <span className="text-sm text-slate-400">—</span>
                        }
                      </td>

                      <td className="px-6 py-4">
                        {s.risk_level
                          ? <RiskBadge level={s.risk_level} />
                          : <span className="text-sm text-slate-400">—</span>
                        }
                      </td>

                      <td className="px-6 py-4 text-sm text-slate-500">
                        {formatDate(s.created_at)}
                      </td>

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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-4">
                <p className="text-sm text-slate-500">
                  Showing{" "}
                  <span className="font-medium text-slate-700">
                    {((currentPage - 1) * PAGE_SIZE) + 1}
                  </span>
                  {" "}–{" "}
                  <span className="font-medium text-slate-700">
                    {Math.min(currentPage * PAGE_SIZE, total)}
                  </span>
                  {" "}of{" "}
                  <span className="font-medium text-slate-700">{total}</span> submissions
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1 || isLoading}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Prev
                  </button>
                  <span className="text-sm font-semibold text-slate-800 px-2">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages || isLoading}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

          </div>
        )}
      </main>
    </div>
  );
}