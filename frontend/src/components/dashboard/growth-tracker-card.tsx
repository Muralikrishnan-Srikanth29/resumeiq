"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { getHistory } from "@/lib/api";
import { HistoryEntry } from "@/lib/types";

export function GrowthTrackerCard() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getHistory(20)
      .then((res) => setHistory(res.history))
      .catch(() => setHistory([]))
      .finally(() => setLoaded(true));
  }, []);

  if (!loaded || history.length < 2) return null;

  const chartData = history.map((h, i) => ({
    run: `#${i + 1}`,
    resume: h.resume_score,
    ats: h.ats_score,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resume Growth Tracker</CardTitle>
        <CardDescription>Score trend across your last {history.length} analyses</CardDescription>
      </CardHeader>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#232838" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="run" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#11151f",
                border: "1px solid #232838",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "#f5f3ed" }}
            />
            <Line type="monotone" dataKey="resume" stroke="#ff6b4a" strokeWidth={2} dot={false} name="Resume Score" />
            <Line type="monotone" dataKey="ats" stroke="#1abc9c" strokeWidth={2} dot={false} name="ATS Score" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
