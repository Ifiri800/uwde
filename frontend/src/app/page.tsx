"use client";

import { FormEvent, useState } from "react";

type AnalysisResult = {
  status: string;
  url: string;
  instruction: string;
  message: string;
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [instruction, setInstruction] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyzeWebsite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url,
          instruction,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.[0]?.msg || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the UWDE backend."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <header className="mb-16">
          <div className="mb-4 inline-flex rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300">
            Universal Web Data Extractor
          </div>

          <h1 className="max-w-4xl text-5xl font-bold tracking-tight sm:text-6xl">
            Extract structured data from almost any website.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">
            Enter a website, describe the information you need, and UWDE
            analyzes the site and extracts the data for you.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
          <h2 className="text-2xl font-semibold">New Extraction</h2>

          <form onSubmit={analyzeWebsite} className="mt-8 space-y-6">
            <div>
              <label
                htmlFor="url"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Website URL
              </label>

              <input
                id="url"
                type="url"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-slate-400"
              />
            </div>

            <div>
              <label
                htmlFor="instruction"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                What information do you want to extract?
              </label>

              <textarea
                id="instruction"
                value={instruction}
                onChange={(event) => setInstruction(event.target.value)}
                rows={5}
                placeholder="Example: Extract job title, company name, location and application URL from every job listing."
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-slate-400"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-white px-6 py-3 font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Analyze Website"}
            </button>
          </form>

          {error && (
            <div className="mt-8 rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {result && (
            <div className="mt-8 rounded-lg border border-emerald-800 bg-emerald-950/30 p-6">
              <h3 className="text-lg font-semibold text-emerald-300">
                Analysis request received
              </h3>

              <div className="mt-4 space-y-2 text-sm text-slate-300">
                <p>
                  <strong>URL:</strong> {result.url}
                </p>

                <p>
                  <strong>Instruction:</strong> {result.instruction}
                </p>

                <p>
                  <strong>Status:</strong> {result.status}
                </p>

                <p>
                  <strong>Message:</strong> {result.message}
                </p>
              </div>
            </div>
          )}
        </section>

        <footer className="mt-12 text-sm text-slate-500">
          UWDE development version 0.1.0
        </footer>
      </div>
    </main>
  );
}