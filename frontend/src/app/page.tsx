"use client";

import { FormEvent, useState } from "react";

type AnalysisResult = {
  status: string;
  url: string;
  final_url: string;
  title: string;
  status_code: number;
  content_type: string;
  headings: string[];
  paragraphs_count: number;
  links_count: number;
  images_count: number;
  lists_count: number;
  tables_count: number;
  instruction: string;
};

type ExtractionResult = {
  status: string;
  url: string;
  final_url: string;
  instruction: string;
  records: Record<string, string>[];
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [instruction, setInstruction] = useState("");

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState("");

  async function analyzeWebsite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setAnalysis(null);
    setExtraction(null);

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
        throw new Error(
          data.detail?.[0]?.msg ||
            data.detail ||
            "Website analysis failed."
        );
      }

      setAnalysis(data);
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

  async function extractData() {
    setExtracting(true);
    setError("");
    setExtraction(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/extract", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: analysis?.final_url || url,
          instruction,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.[0]?.msg ||
            data.detail ||
            "Data extraction failed."
        );
      }

      setExtraction(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to extract data from the website."
      );
    } finally {
      setExtracting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <header className="mb-12">
          <div className="mb-4 inline-flex rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300">
            Universal Web Data Extractor
          </div>

          <h1 className="max-w-4xl text-5xl font-bold tracking-tight sm:text-6xl">
            Extract structured data from almost any website.
          </h1>

          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-400">
            Enter a website, describe the information you need, and UWDE
            analyzes the site and extracts structured data for you.
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
                placeholder="Example: Extract the page title and headings"
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

          {analysis && (
            <section className="mt-10">
              <div className="rounded-xl border border-emerald-800 bg-emerald-950/30 p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-emerald-300">
                      Website Analysis Complete
                    </h3>

                    <p className="mt-1 text-sm text-slate-400">
                      UWDE successfully analyzed the requested website.
                    </p>
                  </div>

                  <span className="rounded-full bg-emerald-900 px-3 py-1 text-sm font-medium text-emerald-300">
                    {analysis.status}
                  </span>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <StatCard label="Page title" value={analysis.title} />
                  <StatCard
                    label="HTTP status"
                    value={String(analysis.status_code)}
                  />
                  <StatCard
                    label="Content type"
                    value={analysis.content_type}
                  />
                  <StatCard
                    label="Headings"
                    value={String(analysis.headings.length)}
                  />
                  <StatCard
                    label="Paragraphs"
                    value={String(analysis.paragraphs_count)}
                  />
                  <StatCard
                    label="Links"
                    value={String(analysis.links_count)}
                  />
                  <StatCard
                    label="Images"
                    value={String(analysis.images_count)}
                  />
                  <StatCard
                    label="Tables"
                    value={String(analysis.tables_count)}
                  />
                </div>

                <div className="mt-6 rounded-lg border border-slate-800 bg-slate-950 p-4">
                  <p className="text-sm text-slate-400">Requested</p>
                  <p className="mt-1 font-medium text-white">
                    {analysis.instruction}
                  </p>

                  <p className="mt-4 text-sm text-slate-400">
                    Final URL
                  </p>
                  <p className="mt-1 break-all text-sm text-slate-300">
                    {analysis.final_url}
                  </p>
                </div>

                {analysis.headings.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold">
                      Detected headings
                    </h4>

                    <ul className="mt-3 space-y-2">
                      {analysis.headings.map((heading, index) => (
                        <li
                          key={`${heading}-${index}`}
                          className="rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-slate-300"
                        >
                          {heading}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  type="button"
                  onClick={extractData}
                  disabled={extracting}
                  className="mt-8 rounded-lg bg-emerald-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {extracting
                    ? "Extracting..."
                    : "Extract Structured Data"}
                </button>
              </div>
            </section>
          )}

          {extraction && (
            <section className="mt-8 rounded-xl border border-blue-800 bg-blue-950/20 p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-blue-300">
                    Extraction Complete
                  </h3>

                  <p className="mt-1 text-sm text-slate-400">
                    {extraction.records.length} record
                    {extraction.records.length === 1 ? "" : "s"} extracted.
                  </p>
                </div>

                <span className="rounded-full bg-blue-900 px-3 py-1 text-sm font-medium text-blue-300">
                  {extraction.status}
                </span>
              </div>

              {extraction.records.length === 0 ? (
                <div className="mt-6 rounded-lg border border-yellow-800 bg-yellow-950/30 p-4 text-yellow-300">
                  No structured records were found for the requested fields.
                </div>
              ) : (
                <div className="mt-6 overflow-x-auto rounded-lg border border-slate-800">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-950">
                      <tr>
                        {Object.keys(extraction.records[0]).map((key) => (
                          <th
                            key={key}
                            className="whitespace-nowrap border-b border-slate-800 px-4 py-3 font-semibold text-slate-300"
                          >
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>

                    <tbody>
                      {extraction.records.map((record, index) => (
                        <tr
                          key={index}
                          className="border-b border-slate-800 last:border-b-0"
                        >
                          {Object.keys(extraction.records[0]).map((key) => (
                            <td
                              key={key}
                              className="max-w-md px-4 py-3 align-top text-slate-300"
                            >
                              {record[key] || ""}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
        </section>

        <footer className="mt-10 text-sm text-slate-500">
          UWDE development version 0.1.0
        </footer>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-2 break-words text-sm font-semibold text-slate-200">
        {value}
      </p>
    </div>
  );
}