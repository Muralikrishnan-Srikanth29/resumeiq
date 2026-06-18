"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResumeInputProps {
  onFileSelected: (file: File) => void;
  onTextChange: (text: string) => void;
  pastedText: string;
  selectedFile: File | null;
  onClearFile: () => void;
}

type InputMode = "upload" | "paste";

export function ResumeInput({
  onFileSelected,
  onTextChange,
  pastedText,
  selectedFile,
  onClearFile,
}: ResumeInputProps) {
  const [mode, setMode] = useState<InputMode>("upload");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const lower = file.name.toLowerCase();
      if (!lower.endsWith(".pdf") && !lower.endsWith(".docx")) {
        alert("Only PDF and DOCX files are supported.");
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div>
      <div className="flex gap-1 mb-4 rounded-lg bg-line/40 p-1 w-fit">
        <button
          type="button"
          onClick={() => setMode("upload")}
          className={cn(
            "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
            mode === "upload" ? "bg-signal text-ink" : "text-slate-light hover:text-paper"
          )}
        >
          Upload file
        </button>
        <button
          type="button"
          onClick={() => setMode("paste")}
          className={cn(
            "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
            mode === "paste" ? "bg-signal text-ink" : "text-slate-light hover:text-paper"
          )}
        >
          Paste text
        </button>
      </div>

      {mode === "upload" && (
        <div>
          {selectedFile ? (
            <div className="flex items-center justify-between rounded-lg border border-verified/40 bg-verified/5 px-4 py-3">
              <div className="flex items-center gap-3">
                <FileText size={20} className="text-verified" />
                <div>
                  <p className="text-sm font-medium text-paper">{selectedFile.name}</p>
                  <p className="text-xs text-slate-light">
                    {(selectedFile.size / 1024).toFixed(0)} KB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClearFile}
                className="text-slate-light hover:text-flag transition-colors"
                aria-label="Remove file"
              >
                <X size={18} />
              </button>
            </div>
          ) : (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const file = e.dataTransfer.files[0];
                if (file) handleFile(file);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-12 cursor-pointer transition-colors",
                isDragging
                  ? "border-signal bg-signal/5"
                  : "border-line hover:border-slate-light"
              )}
            >
              <Upload size={28} className="text-slate-light" />
              <div className="text-center">
                <p className="text-sm font-medium text-paper">
                  Drop your resume here, or click to browse
                </p>
                <p className="text-xs text-slate-light mt-1">PDF or DOCX, up to 5MB</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFile(file);
                }}
              />
            </div>
          )}
        </div>
      )}

      {mode === "paste" && (
        <textarea
          value={pastedText}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder="Paste your full resume text here — including experience, skills, education, and projects..."
          rows={12}
          className="w-full rounded-lg border border-line bg-[#0d111a] px-4 py-3 text-sm text-paper placeholder:text-slate-light/60 focus:border-signal focus:outline-none resize-none font-mono"
        />
      )}
    </div>
  );
}
