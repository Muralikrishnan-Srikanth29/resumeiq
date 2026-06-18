"use client";

interface JDInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function JDInput({ value, onChange }: JDInputProps) {
  return (
    <div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste the job description here to get a match score against this specific role. Leave blank for a general resume evaluation."
        rows={8}
        className="w-full rounded-lg border border-line bg-[#0d111a] px-4 py-3 text-sm text-paper placeholder:text-slate-light/60 focus:border-signal focus:outline-none resize-none font-mono"
      />
      <p className="text-xs text-slate-light mt-2">
        Optional. With a job description, you get a job-fit match score and gap analysis instead of a general evaluation.
      </p>
    </div>
  );
}
