import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { SubmissionListItem, RiskLevel, StatsResponse, HistoryGraphResponse } from "../types";
import UserMenu from "../components/UserMenu";
import { useTheme } from "../context/ThemeContext";
import {
  Shield, Upload, Clock, CheckCircle2,
  XCircle, Loader2, ChevronRight, ChevronLeft,
  FileText, Code2, Trash2, RefreshCw, AlertTriangle,
  BarChart2, Download, LayoutDashboard, Table2
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from "recharts";

// ── Helpers ───────────────────────────────────────────────────────────────────

function RiskBadge({ level }: { level: RiskLevel }) {
  const styles = {
    LOW:    "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    MEDIUM: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    HIGH:   "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
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

// ── Confirm Delete Modal ──────────────────────────────────────────────────────

function ConfirmDeleteModal({
  submission, onConfirm, onCancel, isDeleting,
}: {
  submission: SubmissionListItem;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 text-center mb-1">
          Delete Submission?
        </h2>
        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mb-4">
          Are you sure you want to delete{" "}
          <span className="font-semibold text-slate-700 dark:text-slate-200">"{submission.file1_name}"</span>?
        </p>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-3 mb-6 text-sm text-red-700 dark:text-red-400">
          This will delete the upload and all associated report data. This action cannot be undone.
        </div>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="flex-1 px-4 py-2.5 text-sm font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-xl transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 px-4 py-2.5 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isDeleting ? (
              <><Loader2 className="w-4 h-4 animate-spin" />Deleting...</>
            ) : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function Toast({ message }: { message: string }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-slate-800 dark:bg-slate-700 text-white text-sm font-medium px-4 py-3 rounded-xl shadow-lg">
      <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
      {message}
    </div>
  );
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PAGE_SIZE = 8;

// ── Component ─────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"overview" | "submissions">("overview");

  const [submissions, setSubmissions]     = useState<SubmissionListItem[]>([]);
  const [isLoading, setIsLoading]         = useState(true);
  const [isRefreshing, setIsRefreshing]   = useState(false);
  const [error, setError]                 = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<SubmissionListItem | null>(null);
  const [isDeleting, setIsDeleting]       = useState(false);
  const [toast, setToast]                 = useState<string | null>(null);
  const [currentPage, setCurrentPage]     = useState(1);
  const [totalPages, setTotalPages]       = useState(1);
  const [total, setTotal]                 = useState(0);
  const [modeFilter, setModeFilter]       = useState<"" | "text" | "code">("");
  const [riskFilter, setRiskFilter]       = useState<"" | "LOW" | "MEDIUM" | "HIGH">("");
  const [sortOrder, setSortOrder]         = useState<"desc" | "asc">("desc");
  const [stats, setStats]                 = useState<StatsResponse | null>(null);
  const [graphData, setGraphData]         = useState<HistoryGraphResponse | null>(null);

  const { setAppTheme } = useTheme();
  useEffect(() => {
    setAppTheme();
  }, []);

  const fetchHistory = useCallback(async (page = 1, showRefresh = false) => {
    try {
      showRefresh ? setIsRefreshing(true) : setIsLoading(true);
      setError(null);
      const data = await submissionsApi.getHistory(page, PAGE_SIZE, modeFilter || undefined, riskFilter || undefined, sortOrder);
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

  useEffect(() => { fetchHistory(1); }, [modeFilter, riskFilter, sortOrder, fetchHistory]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await submissionsApi.getStats();
        setStats(data);
      } catch {
        // non-critical
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const data = await submissionsApi.getHistoryGraph();
        setGraphData(data);
      } catch {
        // non-critical
      }
    };
    fetchGraph();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleDeleteConfirm = async () => {
    if (!pendingDelete) return;
    setIsDeleting(true);
    try {
      await submissionsApi.delete(pendingDelete.id);
      setPendingDelete(null);
      setToast("Submission deleted successfully");
      const newTotal    = total - 1;
      const maxPage     = Math.ceil(newTotal / PAGE_SIZE) || 1;
      const pageToFetch = currentPage > maxPage ? maxPage : currentPage;
      await fetchHistory(pageToFetch, true);
    } catch (err) {
      setPendingDelete(null);
      alert(getErrorMessage(err));
    } finally {
      setIsDeleting(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (page < 1 || page > totalPages || page === currentPage) return;
    fetchHistory(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearFilters = () => { setModeFilter(""); setRiskFilter(""); setSortOrder("desc"); };

  const exportCSV = () => {
    const headers = ["ID", "Date", "Mode", "File 1", "File 2", "Similarity", "Risk Level", "Status"];
    const rows = submissions.map(s => [
      s.id,
      formatDate(s.created_at),
      s.mode,
      s.file1_name,
      s.file2_name,
      s.final_similarity !== null ? (s.final_similarity * 100).toFixed(1) + "%" : "—",
      s.risk_level || "—",
      s.status,
    ]);
    const csv  = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `submissions_page_${currentPage}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasActiveFilters = modeFilter || riskFilter || sortOrder !== "desc";

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900">

      {pendingDelete && (
        <ConfirmDeleteModal
          submission={pendingDelete}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setPendingDelete(null)}
          isDeleting={isDeleting}
        />
      )}
      {toast && <Toast message={toast} />}

      {/* Navbar */}
      <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/landing" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800 dark:text-slate-100">Origify</span>
          </Link>
          <UserMenu name={user?.full_name ?? "User"} onLogout={logout} />
        </div>
      </nav>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              Hey, {user?.full_name?.split(" ")[0]}!
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {total > 0
                ? `${total} submission${total !== 1 ? "s" : ""}${hasActiveFilters ? " matching filters" : " total"}`
                : "Welcome back. Ready to run a scan?"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchHistory(currentPage, true)}
              disabled={isRefreshing}
              title="Refresh"
              className="p-2.5 text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={exportCSV}
              disabled={submissions.length === 0}
              title="Export current page as CSV"
              className="p-2.5 text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
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

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-1 mb-6 w-fit shadow-sm">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "overview"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab("submissions")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "submissions"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
            }`}
          >
            <Table2 className="w-4 h-4" />
            Submissions
            {total > 0 && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                activeTab === "submissions"
                  ? "bg-white/20 text-white"
                  : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
              }`}>
                {total}
              </span>
            )}
          </button>
        </div>

        {/* ── Overview Tab ── */}
        {activeTab === "overview" && (
          <div>
            {/* Stats Cards */}
            {stats ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Total Scans</p>
                    <div className="w-8 h-8 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                      <BarChart2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-slate-800 dark:text-slate-100">{stats.total_scans}</p>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Avg Similarity</p>
                    <div className="w-8 h-8 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center">
                      <BarChart2 className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-slate-800 dark:text-slate-100">
                    {(stats.average_similarity * 100).toFixed(1)}%
                  </p>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">High Risk</p>
                    <div className="w-8 h-8 bg-red-50 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-red-600 dark:text-red-400">{stats.high_risk_count}</p>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Most Used</p>
                    <div className="w-8 h-8 bg-green-50 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                      {stats.most_used_mode === "code"
                        ? <Code2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                        : <FileText className="w-4 h-4 text-green-600 dark:text-green-400" />
                      }
                    </div>
                  </div>
                  <p className="text-3xl font-black text-slate-800 dark:text-slate-100 capitalize">{stats.most_used_mode}</p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm animate-pulse">
                    <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3 mb-4" />
                    <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                  </div>
                ))}
              </div>
            )}

            {/* Charts */}
            {graphData && graphData.timeline.length > 1 ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Line Chart */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">Similarity Over Time</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={graphData.timeline} margin={{ top: 4, right: 8, left: -20, bottom: 0 }} style={{ outline: "none" }}>
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "14px", color: "#f1f5f9" }}
                        labelStyle={{ color: "#94a3b8", marginBottom: "4px" }}
                        itemStyle={{ color: "#f1f5f9", fontWeight: 700 }}
                        formatter={(value) => [`${Number(value).toFixed(1)}%`, "Similarity"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="similarity"
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={{ r: 3, fill: "#6366f1" }}
                        activeDot={{ r: 4, fill: "#818cf8", stroke: "none" }}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Bar Chart */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">Risk Distribution</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={[
                        { risk: "Low",    count: graphData.risk_distribution.LOW },
                        { risk: "Medium", count: graphData.risk_distribution.MEDIUM },
                        { risk: "High",   count: graphData.risk_distribution.HIGH },
                      ]}
                      margin={{ top: 4, right: 16, left: -20, bottom: 0 }}
                      barCategoryGap="20%"
                      style={{ outline: "none" }}
                    >
                      <XAxis dataKey="risk" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        cursor={false}
                        contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "14px", color: "#f1f5f9" }}
                        labelStyle={{ color: "#f1f5f9", fontWeight: 700, marginBottom: "4px" }}
                        itemStyle={{ color: "#f1f5f9" }}
                        formatter={(value) => [Number(value), "Submissions"]}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]} isAnimationActive={false} maxBarSize={60}>
                        <Cell fill="#22c55e" />
                        <Cell fill="#eab308" />
                        <Cell fill="#ef4444" />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-16 text-center shadow-sm">
                <div className="w-14 h-14 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <BarChart2 className="w-7 h-7 text-slate-400 dark:text-slate-500" />
                </div>
                <h3 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">No chart data yet</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                  Charts will appear once you have more than one submission
                </p>
                <button
                  onClick={() => navigate("/upload")}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm shadow-sm"
                >
                  Make a submission
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Submissions Tab ── */}
        {activeTab === "submissions" && (
          <div>
            {/* Filters */}
            <div className="flex items-center flex-wrap gap-3 mb-6">
              <select
                value={modeFilter}
                onChange={(e) => setModeFilter(e.target.value as typeof modeFilter)}
                className="text-sm border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg px-3 py-2 text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Modes</option>
                <option value="text">Text</option>
                <option value="code">Code</option>
              </select>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as typeof riskFilter)}
                className="text-sm border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg px-3 py-2 text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Risk Levels</option>
                <option value="LOW">Low Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="HIGH">High Risk</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as "desc" | "asc")}
                className="text-sm border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg px-3 py-2 text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="desc">Newest First</option>
                <option value="asc">Oldest First</option>
              </select>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="text-sm text-slate-400 hover:text-red-500 transition-colors">
                  Clear filters
                </button>
              )}
            </div>

            {/* Content */}
            {error ? (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-xl p-6 text-center">
                <p className="font-medium">{error}</p>
                <button onClick={() => fetchHistory(1)} className="mt-3 text-sm underline">Try again</button>
              </div>
            ) : submissions.length === 0 && !isLoading ? (
              <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-16 text-center shadow-sm">
                <div className="w-14 h-14 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-7 h-7 text-slate-400 dark:text-slate-500" />
                </div>
                <h3 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  {hasActiveFilters ? "No submissions match your filters" : "No submissions yet"}
                </h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                  {hasActiveFilters ? "Try clearing your filters to see all submissions" : "Upload two files to start detecting plagiarism"}
                </p>
                {hasActiveFilters ? (
                  <button onClick={clearFilters} className="bg-slate-600 hover:bg-slate-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm">
                    Clear filters
                  </button>
                ) : (
                  <button onClick={() => navigate("/upload")} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm shadow-sm">
                    Make your first submission
                  </button>
                )}
              </div>
            ) : (
              <div className={`bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm transition-opacity ${isLoading ? "opacity-50 pointer-events-none" : "opacity-100"}`}>
                {isLoading && (
                  <div className="flex items-center justify-center gap-2 py-3 border-b border-slate-100 dark:border-slate-700 bg-indigo-50 dark:bg-indigo-900/20">
                    <Loader2 className="w-3.5 h-3.5 text-indigo-600 animate-spin" />
                    <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">Updating...</span>
                  </div>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Files</th>
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Mode</th>
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Status</th>
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Similarity</th>
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Risk</th>
                        <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-6 py-3">Date</th>
                        <th className="px-6 py-3"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {submissions.map((s) => (
                        <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                          <td className="px-6 py-4">
                            <div className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate max-w-[200px]" title={s.file1_name}>
                              {s.file1_name}
                            </div>
                            <div className="text-xs text-slate-400 dark:text-slate-500 truncate max-w-[200px]" title={s.file2_name}>
                              {s.file2_name}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400">
                              {s.mode === "text" ? <FileText className="w-3.5 h-3.5" /> : <Code2 className="w-3.5 h-3.5" />}
                              <span className="capitalize">{s.mode}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-1.5">
                              <StatusIcon status={s.status} />
                              <span className="text-sm text-slate-600 dark:text-slate-400 capitalize">{s.status}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            {s.final_similarity !== null
                              ? <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{(s.final_similarity * 100).toFixed(1)}%</span>
                              : <span className="text-sm text-slate-400">—</span>
                            }
                          </td>
                          <td className="px-6 py-4">
                            {s.risk_level ? <RiskBadge level={s.risk_level} /> : <span className="text-sm text-slate-400">—</span>}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                            {formatDate(s.created_at)}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-4 justify-end">
                              {s.status === "completed" && (
                                <Link to={`/report/${s.id}`} className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 text-sm font-medium">
                                  Report <ChevronRight className="w-3.5 h-3.5" />
                                </Link>
                              )}
                              <button
                                onClick={() => setPendingDelete(s)}
                                className="text-slate-400 hover:text-red-500 transition-colors"
                                title="Delete submission"
                              >
                                <Trash2 className="w-4 h-4" />
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
                  <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 px-6 py-4">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Showing{" "}
                      <span className="font-medium text-slate-700 dark:text-slate-300">{((currentPage - 1) * PAGE_SIZE) + 1}</span>
                      {" "}–{" "}
                      <span className="font-medium text-slate-700 dark:text-slate-300">{Math.min(currentPage * PAGE_SIZE, total)}</span>
                      {" "}of{" "}
                      <span className="font-medium text-slate-700 dark:text-slate-300">{total}</span> submissions
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1 || isLoading}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
                      >
                        <ChevronLeft className="w-4 h-4" />
                        Prev
                      </button>
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 px-2">
                        {currentPage} / {totalPages}
                      </span>
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages || isLoading}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
                      >
                        Next
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}