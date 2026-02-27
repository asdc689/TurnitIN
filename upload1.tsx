import { useState, useRef, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import {
  Shield, ArrowLeft, Upload, FileText, Code2,
  X, AlertCircle, Loader2, CheckCircle2
} from "lucide-react";

// ── Progress Overlay ──────────────────────────────────────────────────────────

type Step = "uploading" | "queued" | "analyzing" | "done";

function ProgressOverlay({ step }: { step: Step }) {
  const steps: { key: Step; label: string; sublabel: string }[] = [
    { key: "uploading", label: "Uploading Files",    sublabel: "Sending your files to the server..." },
    { key: "queued",    label: "Queued",             sublabel: "Waiting for a worker to pick up the task..." },
    { key: "analyzing", label: "Analyzing",          sublabel: "Running plagiarism detection algorithms..." },
    { key: "done",      label: "Done",               sublabel: "Redirecting to your report..." },
  ];

  const currentIndex = steps.findIndex((s) => s.key === step);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-7 h-7 text-indigo-600 animate-spin" />
          </div>
          <h2 className="text-xl font-bold text-slate-800">Processing Submission</h2>
          <p className="text-slate-500 text-sm mt-1">Please don't close this window</p>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((s, index) => {
            const isCompleted = index < currentIndex;
            const isCurrent   = index === currentIndex;
            const isPending   = index > currentIndex;

            return (
              <div key={s.key} className="flex items-center gap-4">
                {/* Step Icon */}
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-all ${
                  isCompleted ? "bg-green-100" :
                  isCurrent   ? "bg-indigo-100" :
                                "bg-slate-100"
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
                  ) : (
                    <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                  )}
                </div>

                {/* Step Text */}
                <div>
                  <p className={`text-sm font-semibold ${
                    isCompleted ? "text-green-700" :
                    isCurrent   ? "text-indigo-700" :
                                  "text-slate-400"
                  }`}>
                    {s.label}
                  </p>
                  {isCurrent && (
                    <p className="text-xs text-slate-500 mt-0.5">{s.sublabel}</p>
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

// ── File Drop Zone ────────────────────────────────────────────────────────────

function FileDropZone({
  label,
  file,
  onFile,
  onClear,
}: {
  label: string;
  file: File | null;
  onFile: (f: File) => void;
  onClear: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFile(dropped);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-2">{label}</label>
      {file ? (
        <div className="flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-indigo-700 font-medium">
            <CheckCircle2 className="w-4 h-4 text-indigo-500" />
            {file.name}
            <span className="text-indigo-400 font-normal">
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </div>
          <button onClick={onClear} className="text-indigo-400 hover:text-red-500 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? "border-indigo-400 bg-indigo-50"
              : "border-slate-300 hover:border-indigo-400 hover:bg-slate-50"
          }`}
        >
          <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-sm text-slate-600 font-medium">
            Drop your file here, or <span className="text-indigo-600">browse</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Supports .txt, .pdf, .docx, .py, .java, .cpp
          </p>
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".txt,.pdf,.docx,.py,.java,.cpp,.c,.js,.ts"
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          />
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Upload() {
  const navigate = useNavigate();

  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [mode, setMode]   = useState<"text" | "code">("text");
  const [error, setError] = useState<string | null>(null);

  // Progress overlay state
  const [progressStep, setProgressStep] = useState<Step | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (!file1 || !file2) {
      setError("Please upload both files before submitting");
      return;
    }

    try {
      // Step 1: Uploading
      setProgressStep("uploading");
      const data = await submissionsApi.upload(file1, file2, mode);

      // Step 2: Queued
      setProgressStep("queued");
      await delay(800);

      // Step 3: Analyzing
      setProgressStep("analyzing");
      await delay(1200);

      // Step 4: Done
      setProgressStep("done");
      await delay(600);

      // Redirect to report
      navigate(`/report/${data.submission_id}`);

    } catch (err) {
      setProgressStep(null);
      setError(getErrorMessage(err));
    }
  };

  return (
    <>
      {/* Progress Overlay */}
      {progressStep && <ProgressOverlay step={progressStep} />}

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
            <button
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-2xl mx-auto px-6 py-10">

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-800">New Submission</h1>
            <p className="text-slate-500 mt-1">Upload two files to compare for plagiarism</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Mode Toggle */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Comparison Mode</h2>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setMode("text")}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    mode === "text"
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <FileText className="w-5 h-5 shrink-0" />
                  <div className="text-left">
                    <div className="font-semibold text-sm">Text</div>
                    <div className="text-xs opacity-70">Essays, reports, articles</div>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setMode("code")}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    mode === "code"
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <Code2 className="w-5 h-5 shrink-0" />
                  <div className="text-left">
                    <div className="font-semibold text-sm">Code</div>
                    <div className="text-xs opacity-70">Python, Java, C++</div>
                  </div>
                </button>
              </div>
            </div>

            {/* File Upload */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
              <h2 className="text-sm font-semibold text-slate-700">Upload Files</h2>
              <FileDropZone
                label="File 1"
                file={file1}
                onFile={setFile1}
                onClear={() => setFile1(null)}
              />
              <FileDropZone
                label="File 2"
                file={file2}
                onFile={setFile2}
                onClear={() => setFile2(null)}
              />
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
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
              <Upload className="w-4 h-4" />
              Run Analysis
            </button>

          </form>
        </main>
      </div>
    </>
  );
}

// ── Utility ───────────────────────────────────────────────────────────────────

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}