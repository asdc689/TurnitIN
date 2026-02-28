import { useState, useRef, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";
import UserMenu from "../components/UserMenu";
import {
  Shield, ArrowLeft, Upload, FileText,
  Code2, X, AlertCircle, Loader2, CheckCircle2
} from "lucide-react";

// ── Progress Overlay ──────────────────────────────────────────────────────────

type Step = "uploading" | "queued" | "analyzing" | "done";

function ProgressOverlay({ step }: { step: Step }) {
  const steps: { key: Step; label: string; sublabel: string }[] = [
    { key: "uploading", label: "Uploading Files",   sublabel: "Sending your files to the server..." },
    { key: "queued",    label: "Queued",            sublabel: "Waiting for a worker to pick up the task..." },
    { key: "analyzing", label: "Analyzing",         sublabel: "Running plagiarism detection algorithms..." },
    { key: "done",      label: "Done",              sublabel: "Redirecting to your report..." },
  ];

  const currentIndex = steps.findIndex((s) => s.key === step);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md p-8">

        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-indigo-100 dark:bg-indigo-900/40 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-7 h-7 text-indigo-600 dark:text-indigo-400 animate-spin" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Processing Submission</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Please don't close this window</p>
        </div>

        <div className="space-y-4">
          {steps.map((s, index) => {
            const isCompleted = index < currentIndex;
            const isCurrent   = index === currentIndex;

            return (
              <div key={s.key} className="flex items-center gap-4">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-all ${
                  isCompleted ? "bg-green-100 dark:bg-green-900/30" :
                  isCurrent   ? "bg-indigo-100 dark:bg-indigo-900/40" :
                                "bg-slate-100 dark:bg-slate-700"
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 text-indigo-600 dark:text-indigo-400 animate-spin" />
                  ) : (
                    <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-500" />
                  )}
                </div>
                <div>
                  <p className={`text-sm font-semibold ${
                    isCompleted ? "text-green-700 dark:text-green-400" :
                    isCurrent   ? "text-indigo-700 dark:text-indigo-400" :
                                  "text-slate-400 dark:text-slate-500"
                  }`}>
                    {s.label}
                  </p>
                  {isCurrent && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{s.sublabel}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── File Drop Zone ────────────────────────────────────────────────────────────

function FileDropZone({
  label, file, onFile, accept
}: {
  label: string;
  file: File | null;
  onFile: (f: File) => void;
  accept: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      onClick={() => inputRef.current?.click()}
      className="border-2 border-dashed border-slate-200 dark:border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 dark:hover:border-indigo-500 dark:hover:bg-indigo-900/20 transition-all"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.[0]) onFile(e.target.files[0]);
        }}
      />
      {file ? (
        <div className="flex items-center justify-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-500" />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{file.name}</span>
        </div>
      ) : (
        <>
          <Upload className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{label}</p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Click to browse files</p>
        </>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function UploadPage() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode]                 = useState<"text" | "code">("text");
  const [langOverride, setLangOverride] = useState("");
  const [file1, setFile1]               = useState<File | null>(null);
  const [file2, setFile2]               = useState<File | null>(null);
  const [error, setError]               = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState<Step | null>(null);

  const accept = mode === "text" ? ".txt,.pdf,.docx" : ".py,.java,.cpp,.c,.js,.ts";

  const handleModeChange = (newMode: "text" | "code") => {
    setMode(newMode);
    setFile1(null);
    setFile2(null);
    setError(null);
    setLangOverride("");
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (!file1 || !file2) {
      setError("Please select both files before submitting");
      return;
    }

    try {
      setProgressStep("uploading");
      const data = await submissionsApi.upload(
        file1, file2, mode,
        mode === "code" && langOverride ? langOverride : undefined
      );

      setProgressStep("queued");
      setProgressStep("analyzing");
      const submissionId = data.submission_id;

      while (true) {
        await delay(2000);
        const status = await submissionsApi.getStatus(submissionId);

        if (status.status === "completed") {
          setProgressStep("done");
          await delay(600);
          navigate(`/report/${submissionId}`);
          break;
        }

        if (status.status === "failed") {
          setProgressStep(null);
          setError("Analysis failed. Please try again.");
          break;
        }
      }
    } catch (err) {
      setProgressStep(null);
      setError(getErrorMessage(err));
    }
  };

  return (
    <>
      {progressStep && <ProgressOverlay step={progressStep} />}

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
            <UserMenu name={user?.full_name ?? "User"} onLogout={logout} />
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-2xl mx-auto px-6 py-8">

          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>

          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 shadow-sm">

            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-1">New Submission</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mb-8">
              Upload two files to compare for plagiarism
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">

              {/* Mode Selector */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Comparison Mode
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => handleModeChange("text")}
                    className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 font-medium text-sm transition-all ${
                      mode === "text"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400"
                        : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-500"
                    }`}
                  >
                    <FileText className="w-4 h-4" />
                    Text / Document
                  </button>
                  <button
                    type="button"
                    onClick={() => handleModeChange("code")}
                    className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 font-medium text-sm transition-all ${
                      mode === "code"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400"
                        : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-500"
                    }`}
                  >
                    <Code2 className="w-4 h-4" />
                    Source Code
                  </button>
                </div>
              </div>

              {/* Language Override */}
              {mode === "code" && (
                <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-200 dark:border-slate-600">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Programming Language (Optional)
                  </label>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                    We automatically detect the language, but you can force a specific parser.
                  </p>
                  <select
                    value={langOverride}
                    onChange={(e) => setLangOverride(e.target.value)}
                    className="w-full sm:w-1/2 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300"
                  >
                    <option value="">Auto-detect</option>
                    <option value="python">Python</option>
                    <option value="cpp">C / C++</option>
                    <option value="java">Java</option>
                    <option value="javascript">JavaScript</option>
                  </select>
                </div>
              )}

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Upload Files
                  <span className="text-slate-400 dark:text-slate-500 font-normal ml-1">
                    ({mode === "text" ? ".txt, .pdf, .docx" : ".py, .java, .cpp, .c, .js, .ts"})
                  </span>
                </label>
                <div className="space-y-3">
                  <FileDropZone label="File 1 — Click to upload" file={file1} onFile={setFile1} accept={accept} />
                  <FileDropZone label="File 2 — Click to upload" file={file2} onFile={setFile2} accept={accept} />
                </div>
              </div>

              {/* Clear Files */}
              {(file1 || file2) && (
                <button
                  type="button"
                  onClick={() => { setFile1(null); setFile2(null); }}
                  className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                  Clear files
                </button>
              )}

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg p-3 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={!!progressStep || !file1 || !file2}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {progressStep ? (
                  <><Loader2 className="w-4 h-4 animate-spin" />Processing...</>
                ) : (
                  <><Upload className="w-4 h-4" />Analyze Files</>
                )}
              </button>

            </form>
          </div>
        </main>
      </div>
    </>
  );
}